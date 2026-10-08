#include "brainage_flash_trace.h"

#include <cstdlib>
#include <vector>

ArmCpuState g_cpu{};
NdsCpu g_nds_active = NDS_ARM9;
unsigned long long g_runtime_cycles = 0;
uint64_t g_insn_count[2]{};

namespace {
unsigned observations = 0;

void require(bool condition) {
    if (!condition) std::abort();
}

void observe(const NdsCartBackup& chip, uint32_t offset,
    const uint8_t* previous, const uint8_t* committed, uint32_t length,
    uint32_t position, bool last) {
    ++observations;
    require(chip.trace_command_origin.cpu == 9u);
    require(chip.trace_command_origin.pc == 0x02001000u);
    require(chip.trace_command_origin.system_cycles == 100u);
    require(chip.trace_byte_origin.cpu == 7u);
    require(chip.trace_byte_origin.pc == 0x037F9000u);
    require(chip.trace_byte_origin.execution == 2u);
    require(chip.trace_byte_origin.system_cycles == 300u);
    require(offset == 0x180u && length == 1u && position == 4u && last);
    require(previous[0] == 0xFFu && committed[0] == 0x43u);
}
}

int main() {
    g_cpu.R[15] = 0x02001000u;
    g_runtime_cycles = 200u;
    NdsCartBackupOrigin native = task_a_capture_origin();
    require(native.valid && native.pc == 0x02001000u && native.cpu == 9u);
    require(native.execution == 1u && native.system_cycles == 100u);
    {
        TaskAHardwareScope hardware;
        require(!task_a_capture_origin().valid);
    }
    require(task_a_capture_origin().valid);
    NdsCartBackup chip;
    chip.config.type = NdsCartridgeSaveType::Flash;
    chip.config.size = 262144u;
    chip.sram.assign(chip.config.size, 0xFFu);
    nds_cart_backup_spi_write(chip, 0x06u, 0u, true);
    nds_cart_backup_spi_write(chip, 0x0Au, 0u, false, &native, observe);
    g_nds_active = NDS_ARM7;
    g_runtime_cycles = 300u;
    g_cpu.R[15] = 0xDEADBEEFu;
    {
        TaskAInstructionScope interpreted(0x037F9000u, false);
        NdsCartBackupOrigin current = task_a_capture_origin();
        require(current.valid && current.pc == 0x037F9000u);
        {
            TaskAInstructionScope nested(0x037F9004u, true);
            require(task_a_capture_origin().pc == 0x037F9004u);
            require(task_a_capture_origin().thumb);
        }
        require(task_a_capture_origin().pc == 0x037F9000u);
        nds_cart_backup_spi_write(chip, 0u, 1u, false, &current, observe);
        nds_cart_backup_spi_write(chip, 1u, 2u, false, &current, observe);
        nds_cart_backup_spi_write(chip, 0x80u, 3u, false, &current, observe);
        nds_cart_backup_spi_write(chip, 0x43u, 4u, true, &current, observe);
    }
    require(observations == 1u && chip.dirty && chip.sram[0x180u] == 0x43u);
    require(task_a_capture_origin().pc == 0xDEADBEEFu);
    nds_cart_backup_reset_command(chip);
    require(!chip.trace_command_origin.valid && !chip.trace_byte_origin.valid);
    std::puts("TASK_A_ORIGIN_TEST_OK");
}
