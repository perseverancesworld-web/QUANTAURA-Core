from quantaura.policy.approvals import ApprovalManager, RolePolicy


def test_role_gate():
    mgr = ApprovalManager(RolePolicy(required_roles={"ops", "risk"}, min_actors=2))
    r1 = mgr.add_approval([], required=2, actor="alice", decision="approve", role="ops")
    assert not r1.complete
    r2 = mgr.add_approval(r1.approvals, required=2, actor="bob", decision="approve", role="risk")
    assert r2.complete and r2.authorized


def test_reject_short_circuits():
    mgr = ApprovalManager()
    r = mgr.add_approval([], required=2, actor="carol", decision="reject")
    assert r.complete and not r.authorized
