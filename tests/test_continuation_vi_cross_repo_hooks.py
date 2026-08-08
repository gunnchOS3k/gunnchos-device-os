"""Cont VI cross-repo hook probe."""
from gunnchos_device_os.cross_repo_cont_vi_hooks import probe_hooks


def test_cross_repo_hooks_do_not_claim_full_platform():
    report = probe_hooks()
    assert report["full_gunnchos_platform_digital_complete"] is False
    assert report["present_count"] >= 0
    assert len(report["hooks"]) >= 4
