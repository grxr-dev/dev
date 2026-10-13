#pragma once
#include <memory>
#include "model.h"

namespace task_aw2 {
struct Ledger {
    std::vector<Observation> expected;
    size_t cursor=0;
    unsigned instructions=0;
    std::string failure;
    explicit Ledger(const Snapshot& entry):expected(transcript(entry)) {}
    bool accept(const Observation& actual) noexcept {
        if (!failure.empty()) return false;
        try {
            require(cursor<expected.size(), "extra event after terminal");
            require(actual.kind!=task_aw::Kind::irq && actual.kind!=task_aw::Kind::scheduler &&
                    actual.kind!=task_aw::Kind::device && actual.kind!=task_aw::Kind::arm7,
                    "forbidden scheduler/device/IRQ/ARM7 service");
            if (actual.kind==task_aw::Kind::instruction) {
                require(instructions<pcs.size(), "extra candidate instruction");
                prospective(actual.state,instructions);
            }
            require(same(actual,expected[cursor]), "unexpected/missing/duplicate/out-of-order transcript event");
            canonical(actual.state);
            if (actual.kind==task_aw::Kind::instruction) ++instructions;
            ++cursor;
            return true;
        } catch (const std::exception& error) { failure=error.what(); }
        catch (...) { failure="unknown ledger failure"; }
        return false;
    }
    bool complete() const { return failure.empty() && cursor==expected.size() && instructions==12; }
    bool finish() {
        if (complete()) return true;
        if (failure.empty()) failure="missing candidate instruction/event at terminal";
        return false;
    }
};
using PassiveSource=Snapshot (*)();
inline void audit_snapshot(FILE* output, const Snapshot& snapshot) {
    const auto bytes=canonical(snapshot);
    std::fprintf(output,"{\"event\":\"canonical_snapshot\",\"sha256\":\"%s\",\"canonical_hex\":\"",digest(snapshot).c_str());
    for (auto byte:bytes) std::fprintf(output,"%02x",unsigned(byte));
    std::fputs("\"}\n",output);
    require(std::ferror(output)==0, "audit snapshot write");
}
class Controller {
    FILE* output=nullptr;
    PassiveSource source=nullptr;
    std::unique_ptr<Ledger> ledger;
    inline static Controller* active=nullptr;
    [[noreturn]] void terminate(bool success, const std::string& reason) noexcept {
        if (output) {
            std::fprintf(output,"{\"event\":\"%s\",\"events\":%zu,\"reason\":\"",
                         success ? "terminal" : "failure",ledger ? ledger->cursor : 0);
            for (unsigned char character:reason) {
                if (character=='"' || character=='\\') std::fputc('\\',output);
                if (character<32) std::fprintf(output,"\\u%04x",unsigned(character));
                else std::fputc(character,output);
            }
            std::fputs("\"}\n",output);
            if (std::ferror(output)) task_aw::dispose(output,78);
        }
        task_aw::dispose(output,success ? 73 : 79);
    }
    static void receive(const task_aw::Event& event) {
        require(active!=nullptr, "missing controller owner");
        active->observe(event);
    }
public:
    void start(FILE* audit, PassiveSource passive) {
        output=audit;
        source=passive;
        try {
            require(output && source && !active && !task_aw::observer, "audit/provider/observer ownership");
            const auto snapshot=source();
            audit_snapshot(output,snapshot);
            ledger=std::make_unique<Ledger>(snapshot);
            std::fprintf(output,"{\"event\":\"preflight\",\"manifest_sha256\":\"%s\",\"planned_events\":%zu}\n",
                         digest(au_manifest()).c_str(),ledger->expected.size());
            active=this;
            task_aw::audit=output;
            task_aw::observer=receive;
        } catch (const std::exception& error) { terminate(false,error.what()); }
        catch (...) { terminate(false,"unknown preflight failure"); }
    }
    void observe(const task_aw::Event& event) {
        try {
            require(ledger!=nullptr && source!=nullptr, "unarmed controller");
            const auto snapshot=source();
            Observation actual{event.kind,event.pc,event.address,event.width,event.value,event.write,snapshot};
            std::fprintf(output,"{\"event\":\"observation\",\"index\":%zu,\"kind\":%u,\"pc\":%u,\"address\":%u,"
                         "\"width\":%u,\"value\":%u,\"write\":%s,\"cycle9\":%llu,\"state_sha256\":\"%s\"}\n",
                         ledger->cursor,unsigned(event.kind),event.pc,event.address,event.width,event.value,
                         event.write ? "true" : "false",static_cast<unsigned long long>(snapshot.get("cycle9")),
                         digest(snapshot).c_str());
            require(std::ferror(output)==0, "audit observation write");
            if (!ledger->accept(actual)) {
                audit_snapshot(output,snapshot);
                terminate(false,ledger->failure);
            }
            if (ledger->complete()) {
                audit_snapshot(output,snapshot);
                terminate(true,"complete transcript; before IRQ and scheduler tail");
            }
        } catch (const std::exception& error) { terminate(false,error.what()); }
        catch (...) { terminate(false,"unknown observation failure"); }
    }
    [[noreturn]] void end_stream() {
        const bool success=ledger && ledger->finish();
        terminate(success,success ? "complete" : ledger ? ledger->failure : "unarmed stream ended");
    }
};
inline Snapshot reject_legacy_copy(const task_aw::Snapshot&) {
    throw std::runtime_error("AW raw copies have no canonical cap/timing/readiness provider; live AX denied");
}
}
