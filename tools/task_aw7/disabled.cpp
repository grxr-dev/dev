#include <iostream>
#include "aw7/integration.h"
int main() {
    if (task_aw7::waiting() || task_aw7::owns() || task_aw::observer) return 1;
    bool rejected=false;
    try { task_aw7::arm_diagnostic(); } catch (const std::exception&) { rejected=true; }
    if (!rejected || task_aw7::waiting() || task_aw7::owns() || task_aw::observer || task_aw3::armed) return 2;
    std::cout<<"PASS default compile: no arming API, owner, observer or provider activity\n";
    return 0;
}
