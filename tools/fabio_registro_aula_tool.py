"""Restricted LA Music lesson-registration tools for Fábio webhook routes.

These tools intentionally expose only the minimum capabilities needed by the
LA Teacher app webhook: fetch aula context, transcribe a trusted Supabase audio
URL, and create a pending lesson record through the dedicated Supabase RPC.
They do NOT expose arbitrary SQL, shell, filesystem, or generic HTTP writes.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from tools.registry import registry

_TOOLSET = "fabio_registro_aula"
_DEFAULT_SUPABASE_URL = "https://ouqwbbermlzqqvtqwlul.supabase.co"
_MAX_AUDIO_BYTES = int(os.getenv("FABIO_AUDIO_MAX_BYTES", str(80 * 1024 * 1024)))
_HTTP_TIMEOUT = (10, 120)


def _supabase_url() -> str:
    return (os.getenv("LAREPORT_SUPABASE_URL") or _DEFAULT_SUPABASE_URL).rstrip("/")


def _service_role() -> str:
    return os.getenv("LAREPORT_SUPABASE_SERVICE_ROLE") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""


def _headers(prefer: str | None = None) -> Dict[str, str]:
    key = _service_role()
    if not key:
        raise RuntimeError("LAREPORT_SUPABASE_SERVICE_ROLE is not configured")
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _safe_json_response(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text[:4000]


def check_requirements() -> bool:
    return bool(_service_role())


def _validate_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("audio_url must be https")
    if not parsed.netloc:
        raise ValueError("audio_url missing host")
    # The app currently sends temporary Supabase Storage URLs. Keep the guard
    # permissive enough for signed Supabase host variants, but reject obvious
    # localhost/private shortcut hosts.
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("audio_url host is not allowed")


def fabio_buscar_contexto_aula(aula_id: int, professor_id: int | None = None) -> str:
    """Return rows from vw_fabio_aulas_contexto for one aula.

    The returned rows let the agent map named students to aluno_id and, for
    group classes, to each student's own aula_local_id for the RPC fatias.
    """
    params: Dict[str, str] = {
        "aula_local_id": f"eq.{int(aula_id)}",
        "select": "aula_local_id,aula_emusys_id,unidade_id,unidade_codigo,unidade_nome,data_aula,data_hora_inicio,data_hora_fim,horario_inicio_brt,horario_fim_brt,aula_tipo,aula_categoria,turma_nome,curso_nome,sala_nome,professor_id,professor_nome,aluno_id,aluno_nome,presenca_status,cancelada,nr_da_aula,qtd_alunos,anotacoes_fabio,qualidade_contexto",
        "order": "aluno_nome.asc",
    }
    if professor_id is not None:
        params["professor_id"] = f"eq.{int(professor_id)}"
    url = f"{_supabase_url()}/rest/v1/vw_fabio_aulas_contexto"
    resp = requests.get(url, headers=_headers(), params=params, timeout=_HTTP_TIMEOUT)
    data = _safe_json_response(resp)
    if resp.status_code >= 400:
        return json.dumps({"ok": False, "status_code": resp.status_code, "error": data}, ensure_ascii=False)
    return json.dumps({"ok": True, "rows": data}, ensure_ascii=False)


def fabio_transcrever_audio_url(audio_url: str, language: str | None = "pt") -> str:
    """Download and transcribe a temporary Supabase audio URL with local Whisper."""
    _validate_https_url(audio_url)
    with requests.get(audio_url, stream=True, timeout=_HTTP_TIMEOUT) as resp:
        if resp.status_code >= 400:
            return json.dumps({"ok": False, "status_code": resp.status_code, "error": resp.text[:1000]}, ensure_ascii=False)
        suffix = Path(urlparse(audio_url).path).suffix or ".audio"
        total = 0
        with tempfile.NamedTemporaryFile(prefix="fabio_audio_", suffix=suffix, delete=False) as f:
            tmp_path = f.name
            try:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > _MAX_AUDIO_BYTES:
                        return json.dumps({"ok": False, "error": "audio too large", "max_bytes": _MAX_AUDIO_BYTES}, ensure_ascii=False)
                    f.write(chunk)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
    try:
        from faster_whisper import WhisperModel

        model_name = os.getenv("FABIO_WHISPER_MODEL") or os.getenv("HERMES_STT_LOCAL_MODEL") or "base"
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, info = model.transcribe(tmp_path, language=language or None, vad_filter=True)
        parts: List[str] = []
        for seg in segments:
            text = (getattr(seg, "text", "") or "").strip()
            if text:
                parts.append(text)
        text = " ".join(parts).strip()
        used_vad = True

        # WebM/Opus gravado pelo browser pode ser classificado como não-fala
        # pelo VAD do faster-whisper mesmo com áudio válido. Se o VAD remover
        # tudo, refaz uma única vez sem VAD. Isso preserva o guardrail: não
        # inventa conteúdo, só evita falso vazio do transcritor.
        if not text:
            segments, info = model.transcribe(tmp_path, language=language or None, vad_filter=False)
            parts = []
            for seg in segments:
                text = (getattr(seg, "text", "") or "").strip()
                if text:
                    parts.append(text)
            text = " ".join(parts).strip()
            used_vad = False

        return json.dumps({
            "ok": True,
            "text": text,
            "language": getattr(info, "language", None),
            "duration": getattr(info, "duration", None),
            "bytes": total,
            "vad_filter": used_vad,
            "model": model_name,
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": f"transcription_failed: {type(e).__name__}: {e}"}, ensure_ascii=False)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def fabio_atualizar_status_audio(audio_id: str, status: str, erro: str | None = None) -> str:
    """Update only the queue status for one Fábio audio row.

    This is intentionally narrow: no arbitrary SQL, no table choice, and only
    the lifecycle states used by the audio queue.
    """
    allowed = {"pendente", "transcrevendo", "transcrito", "normalizado", "erro"}
    if status not in allowed:
        return json.dumps({"ok": False, "error": "invalid status", "allowed": sorted(allowed)}, ensure_ascii=False)
    if not audio_id:
        return json.dumps({"ok": False, "error": "audio_id is required"}, ensure_ascii=False)

    url = f"{_supabase_url()}/rest/v1/fabio_fila_audios"
    body: Dict[str, Any] = {"status": status, "atualizado_em": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    body["erro"] = erro[:500] if erro else None
    resp = requests.patch(url, headers=_headers(prefer="return=representation"), params={"id": f"eq.{audio_id}"}, json=body, timeout=_HTTP_TIMEOUT)
    data = _safe_json_response(resp)
    if resp.status_code >= 400:
        return json.dumps({"ok": False, "status_code": resp.status_code, "error": data}, ensure_ascii=False)
    return json.dumps({"ok": True, "status_code": resp.status_code, "result": data}, ensure_ascii=False)


def _has_pedagogical_content(value: Any) -> bool:
    """Return True if payload carries real teacher-derived content.

    Structural labels, ids and empty placeholders do not count. This prevents
    empty transcriptions from creating fake/blank lesson records.
    """
    if value is None:
        return False
    if isinstance(value, str):
        t = value.strip()
        if not t or t in {"—", "-", "null", "None"}:
            return False
        placeholders = ["a completar com o professor", "transcrição vazia", "transcricao vazia"]
        return not any(p in t.lower() for p in placeholders)
    if isinstance(value, dict):
        ignored = {"audio_id", "aula_id", "professor_id", "aluno_id", "origem", "molde", "presenca", "status"}
        return any(_has_pedagogical_content(v) for k, v in value.items() if k not in ignored)
    if isinstance(value, list):
        return any(_has_pedagogical_content(v) for v in value)
    return False


def fabio_criar_registro_aula(p_payload: Dict[str, Any]) -> str:
    """Call only public.fabio_criar_registro(p_payload jsonb) via Supabase REST."""
    if not isinstance(p_payload, dict):
        return json.dumps({"ok": False, "error": "p_payload must be an object"}, ensure_ascii=False)
    required = ["aula_id", "professor_id", "origem", "molde", "tronco", "fatias"]
    missing = [k for k in required if k not in p_payload]
    if missing:
        return json.dumps({"ok": False, "error": "missing required keys", "missing": missing}, ensure_ascii=False)
    if p_payload.get("origem") != "app":
        return json.dumps({"ok": False, "error": "origem must be 'app' for this route"}, ensure_ascii=False)

    audio_id = str(p_payload.get("audio_id") or "")
    content_probe = {
        "tronco": p_payload.get("tronco"),
        "fatias": p_payload.get("fatias"),
        "texto_consolidado": p_payload.get("texto_consolidado"),
    }
    if not _has_pedagogical_content(content_probe):
        if audio_id:
            fabio_atualizar_status_audio(audio_id, "erro", "transcricao vazia; professor precisa regravar")
        return json.dumps({"ok": False, "error": "sem conteúdo pedagógico real; registro não criado", "audio_id": audio_id or None}, ensure_ascii=False)

    url = f"{_supabase_url()}/rest/v1/rpc/fabio_criar_registro"
    body = {"p_payload": p_payload}
    resp = requests.post(url, headers=_headers(), json=body, timeout=_HTTP_TIMEOUT)
    data = _safe_json_response(resp)
    if resp.status_code >= 400:
        if audio_id:
            fabio_atualizar_status_audio(audio_id, "erro", f"rpc fabio_criar_registro {resp.status_code}")
        return json.dumps({"ok": False, "status_code": resp.status_code, "error": data}, ensure_ascii=False)
    if audio_id:
        fabio_atualizar_status_audio(audio_id, "normalizado", None)
    return json.dumps({"ok": True, "status_code": resp.status_code, "result": data}, ensure_ascii=False)


registry.register(
    name="fabio_buscar_contexto_aula",
    toolset=_TOOLSET,
    description="Busca contexto pedagógico restrito de uma aula na view vw_fabio_aulas_contexto.",
    emoji="🎼",
    requires_env=["LAREPORT_SUPABASE_SERVICE_ROLE"],
    check_fn=check_requirements,
    schema={
        "name": "fabio_buscar_contexto_aula",
        "description": "Busca, por aula_id, os alunos e metadados necessários para montar tronco/fatias do registro de aula. Não executa SQL livre.",
        "parameters": {
            "type": "object",
            "properties": {
                "aula_id": {"type": "integer", "description": "aula_local_id / PK da aula no LA Report"},
                "professor_id": {"type": "integer", "description": "ID interno do professor, opcional para validação"},
            },
            "required": ["aula_id"],
        },
    },
    handler=lambda args, **kw: fabio_buscar_contexto_aula(args.get("aula_id"), args.get("professor_id")),
)

registry.register(
    name="fabio_transcrever_audio_url",
    toolset=_TOOLSET,
    description="Transcreve áudio temporário do Supabase Storage usando Whisper local.",
    emoji="🎙️",
    requires_env=["LAREPORT_SUPABASE_SERVICE_ROLE"],
    check_fn=check_requirements,
    schema={
        "name": "fabio_transcrever_audio_url",
        "description": "Baixa e transcreve um audio_url HTTPS temporário (Supabase Storage). Retorna texto transcrito; não expõe acesso genérico a arquivos ou terminal.",
        "parameters": {
            "type": "object",
            "properties": {
                "audio_url": {"type": "string", "description": "URL HTTPS temporária do áudio"},
                "language": {"type": "string", "description": "Código do idioma para Whisper; padrão pt"},
            },
            "required": ["audio_url"],
        },
    },
    handler=lambda args, **kw: fabio_transcrever_audio_url(args.get("audio_url", ""), args.get("language", "pt")),
)

registry.register(
    name="fabio_atualizar_status_audio",
    toolset=_TOOLSET,
    description="Atualiza somente o status de um áudio na fila Fábio.",
    emoji="🧾",
    requires_env=["LAREPORT_SUPABASE_SERVICE_ROLE"],
    check_fn=check_requirements,
    schema={
        "name": "fabio_atualizar_status_audio",
        "description": "Marca um audio_id da fabio_fila_audios como normalizado ou erro. Use para encerrar fila quando transcrição falhar ou depois de registro criado.",
        "parameters": {
            "type": "object",
            "properties": {
                "audio_id": {"type": "string", "description": "UUID do áudio na fila"},
                "status": {"type": "string", "enum": ["pendente", "transcrevendo", "transcrito", "normalizado", "erro"]},
                "erro": {"type": "string", "description": "Mensagem curta quando status=erro"},
            },
            "required": ["audio_id", "status"],
        },
    },
    handler=lambda args, **kw: fabio_atualizar_status_audio(args.get("audio_id", ""), args.get("status", ""), args.get("erro")),
)

registry.register(
    name="fabio_criar_registro_aula",
    toolset=_TOOLSET,
    description="Chama exclusivamente a RPC Supabase fabio_criar_registro para criar registro aguardando confirmação.",
    emoji="✅",
    requires_env=["LAREPORT_SUPABASE_SERVICE_ROLE"],
    check_fn=check_requirements,
    schema={
        "name": "fabio_criar_registro_aula",
        "description": "Grava o registro normalizado chamando somente public.fabio_criar_registro(p_payload). Use status aguardando_confirmacao via RPC; não escreve direto em tabelas.",
        "parameters": {
            "type": "object",
            "properties": {
                "p_payload": {
                    "type": "object",
                    "description": "Payload completo com audio_id, aula_id, professor_id, origem='app', molde, tronco e fatias.",
                }
            },
            "required": ["p_payload"],
        },
    },
    handler=lambda args, **kw: fabio_criar_registro_aula(args.get("p_payload")),
)
