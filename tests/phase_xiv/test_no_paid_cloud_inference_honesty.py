"""Device OS tip honesty: no paid/cloud inference and no deploy claims."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "local_ai" / "NO_PAID_CLOUD_INFERENCE_HONESTY.json"
NANO = ROOT / "artifacts" / "local_ai" / "VP_LOCAL_AI_NANO_FALLBACK.json"


def test_no_paid_cloud_inference_honesty_stamp():
    doc = json.loads(STAMP.read_text(encoding="utf-8"))
    assert doc["schema"] == "gunnchos.device_os.no_paid_cloud_inference_honesty_v1"
    assert doc["tip_floor"] == "b6860a6"
    assert doc["paid_cloud_inference_invoked"] is False
    assert doc["openai_api_called"] is False
    assert doc["anthropic_api_called"] is False
    assert doc["cloud_endpoint_called"] is False
    assert doc["production_deploy_claimed"] is False
    assert doc["local_only"] is True
    assert doc["local_fast_claimed"] is False
    assert doc["local_pro_claimed"] is False
    assert doc["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert doc["HUMAN"] is False
    assert doc["HUMAN_E6"] is False
    assert doc["RC2"] is False
    assert doc["V1"] is False
    assert doc["gates"]["NO_PAID_CLOUD_INFERENCE"] is True
    assert doc["gates"]["NO_PRODUCTION_DEPLOY_CLAIM"] is True
    assert doc["gates"]["ABSENT_SIBLING_NEQ_PAID_INFERENCE"] is True
    assert doc["gates"]["ABSENT_SIBLING_NEQ_PRODUCT_COMPLETE"] is True
    sibling = doc["absent_sibling_gunnchai"]
    assert sibling["compat_bridge_authorizes_paid_inference"] is False
    assert sibling["compat_bridge_claims_product_complete"] is False
    assert sibling["sandbox_network_unrestricted"] is False
    assert sibling["lane_c_tip_floor"] == "b6860a6"


def test_nano_fallback_companion_stays_incomplete():
    nano = json.loads(NANO.read_text(encoding="utf-8"))
    assert nano["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert nano["HUMAN_E6"] is False
    assert nano["intelligence"]["fast"]["present"] is False
    assert nano["intelligence"]["pro"]["present"] is False
    assert nano["mislabel_rejected"] is True
