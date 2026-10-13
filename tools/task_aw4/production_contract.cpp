#include "aw3/bridge.h"
void production_contract(const task_aw2::Snapshot& snapshot) {
#if defined(AW4_EXPECT_OVERRIDE_REJECTION)
    task_aw3::entry_preflight(snapshot,snapshot);
#else
    task_aw3::entry_preflight(snapshot);
#endif
}
