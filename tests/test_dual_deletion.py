import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.storage import (
    create_match,
    get_match,
    list_matches,
    get_active_matches,
    delete_match,
    restore_match_to_screen,
    end_match,
    _matches_cache
)
from database.mongo import get_db, SPORT_COLLECTIONS


async def test_dual_deletion_behavior():
    print("==================================================")
    print("TESTING DUAL MATCH DELETION & SCREEN CLEARING")
    print("==================================================")

    # ----------------------------------------------------
    # TEST 1: UNCONCLUDED MATCH
    # Must be deleted from BOTH screen AND database
    # ----------------------------------------------------
    print("\n--- TEST 1: Unconcluded Match Deletion ---")
    m_unconcluded = await create_match(
        sport_id="badminton",
        team_a_code="amsc",
        team_b_code="ppe",
        venue="Court 1",
        stage="Test Unconcluded"
    )
    uid = m_unconcluded["id"]
    print(f"Created unconcluded match: {uid}, status: {m_unconcluded.get('status')}")
    assert m_unconcluded.get("status") in ["upcoming", "squads_announced", "live"]

    # Verify present before deletion
    assert get_match(uid) is not None
    active_ids = [m["id"] for m in get_active_matches()]
    assert uid in active_ids

    # Perform delete
    del_res = await delete_match(uid)
    print(f"Delete result for unconcluded match: {del_res}")

    assert del_res.get("deleted_from_db") is True
    assert del_res.get("concluded") is False

    # Verify removed from memory cache
    assert uid not in _matches_cache

    # Verify removed from screen lists
    screen_ids = [m["id"] for m in list_matches(include_hidden=False)]
    assert uid not in screen_ids
    active_ids_after = [m["id"] for m in get_active_matches()]
    assert uid not in active_ids_after

    # Verify removed from database collections
    db = get_db()
    if db is not None:
        for col in SPORT_COLLECTIONS:
            doc = db[col].find_one({"id": uid})
            assert doc is None, f"Match {uid} should not exist in mongo {col}"
        print("✓ Verified match permanently deleted from MongoDB Atlas collections!")
    print("✓ Test 1 passed: Unconcluded match erased from screen and database.")

    # ----------------------------------------------------
    # TEST 2: CONCLUDED MATCH
    # Must be cleared from SCREEN ONLY, and KEPT in DATABASE
    # ----------------------------------------------------
    print("\n--- TEST 2: Concluded Match Screen-Clear ---")
    m_concluded = await create_match(
        sport_id="carrom",
        team_a_code="ppe",
        team_b_code="ppt",
        venue="Indoor Hall",
        stage="Test Concluded"
    )
    cid = m_concluded["id"]
    # Conclude the match
    m_concluded = await end_match(
        match_id=cid,
        winner="team_a",
        result_summary="PPE won the championship board!",
        motm="PPE Champion"
    )
    assert m_concluded.get("status") == "completed"
    print(f"Concluded match: {cid}, status: {m_concluded.get('status')}")

    # Prior to clearing, should be in list_matches()
    all_before = [m["id"] for m in list_matches(include_hidden=False)]
    assert cid in all_before

    # Perform delete on concluded match
    clear_res = await delete_match(cid)
    print(f"Delete/Clear result for concluded match: {clear_res}")

    assert clear_res.get("deleted_from_db") is False
    assert clear_res.get("concluded") is True

    # Verify cleared from active screen
    all_after = [m["id"] for m in list_matches(include_hidden=False)]
    assert cid not in all_after, f"Match {cid} must NOT be in active list_matches()!"
    active_after = [m["id"] for m in get_active_matches()]
    assert cid not in active_after, f"Match {cid} must NOT be in get_active_matches()!"

    # Verify STILL PRESERVED in database!
    if db is not None:
        found_in_db = False
        for col in SPORT_COLLECTIONS:
            doc = db[col].find_one({"id": cid})
            if doc is not None:
                found_in_db = True
                assert doc.get("hidden_from_screen") is True
                assert doc.get("status") == "completed"
                assert doc.get("winner_code") == "ppe"
                print(f"✓ Verified match {cid} remains preserved in MongoDB collection '{col}' with hidden_from_screen=True!")
        assert found_in_db, "Concluded match must NOT be deleted from database!"

    # Verify accessible in raw archive query
    archive_matches = [m for m in list_matches(limit=100, include_hidden=True) if m.get("hidden_from_screen")]
    archive_ids = [m["id"] for m in archive_matches]
    assert cid in archive_ids, "Match must be accessible in database archive query!"
    print("✓ Test 2 passed: Concluded match cleared only from screen, and preserved in database.")

    # ----------------------------------------------------
    # TEST 3: RESTORE MATCH BACK TO SCREEN
    # ----------------------------------------------------
    print("\n--- TEST 3: Restore Match To Screen ---")
    restored = await restore_match_to_screen(cid)
    assert restored.get("hidden_from_screen") is False
    screen_ids_after_restore = [m["id"] for m in list_matches(include_hidden=False)]
    assert cid in screen_ids_after_restore
    print("✓ Test 3 passed: Match successfully restored to active screen!")

    # Cleanup test concluded match from DB
    restored["status"] = "upcoming"  # set to unconcluded so we can cleanly delete from DB
    _matches_cache[cid] = restored
    await delete_match(cid)
    print("✓ Test cleanup completed.")

    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(test_dual_deletion_behavior())
