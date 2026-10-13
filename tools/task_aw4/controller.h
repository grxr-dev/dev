#pragma once
#include <memory>
#include "reconcile.h"
namespace task_aw4 {
class Controller {
    FILE* output=nullptr;
    task_aw2::PassiveSource source=nullptr;
    std::unique_ptr<Ledger> ledger;
    inline static Controller* active=nullptr;
    [[noreturn]] void dispose(bool success,const std::string& reason) noexcept {
        if (output) {
            std::fprintf(output,"{\"event\":\"%s\",\"events\":%zu,\"reason\":\"",
                success ? "terminal" : "failure",ledger ? ledger->cursor : 0);
            for (unsigned char character:reason) {
                if (character=='"' || character=='\\') std::fputc('\\',output);
                if (character<32) std::fprintf(output,"\\u%04x",unsigned(character));
                else std::fputc(character,output);
            }
            std::fputs("\"}\n",output);
        }
        task_aw::dispose(output,output && !std::ferror(output) ? success ? 73 : 79 : 78);
    }
    static void receive(const task_aw::Event& event) {
        require(active,"missing reconciled controller");
        active->observe(event);
    }
    void bind(FILE* file,task_aw2::PassiveSource passive,const Snapshot& authority) {
        output=file; source=passive;
        try {
            require(output && source && !active && !task_aw::observer,"controller ownership");
            const auto observed=source();
            task_aw2::audit_snapshot(output,observed);
            ledger=std::make_unique<Ledger>(observed,authority);
            require(source()==observed,"immutable entry changed before observer ownership");
            std::fprintf(output,"{\"event\":\"preflight\",\"manifest\":\"%s\",\"entry\":\"%s\",\"seal\":\"%s\",\"events\":77}\n",
                task_aw2::digest(authority).c_str(),ledger->previous.c_str(),ledger->seal_digest.c_str());
            active=this; task_aw::audit=output; task_aw::observer=receive;
        } catch (const std::exception& error) { dispose(false,error.what()); }
        catch (...) { dispose(false,"unknown binding failure"); }
    }
public:
    void start(FILE* file,task_aw2::PassiveSource passive) { bind(file,passive,task_aw2::au_manifest()); }
#if defined(AW4_ROMFREE_CERTIFICATION)
    void test_only_start(FILE* file,task_aw2::PassiveSource passive,const Snapshot& authority) { bind(file,passive,authority); }
#endif
    void observe(const task_aw::Event& event) {
        try {
            require(ledger && source,"unarmed observation");
            Observation actual{event.kind,event.pc,event.address,event.width,event.value,event.write,source()};
            const auto predecessor=ledger->previous;
            const auto index=ledger->cursor;
            task_aw2::audit_snapshot(output,actual.state);
            const bool accepted=ledger->accept(actual,predecessor);
            std::fprintf(output,"{\"event\":\"observation\",\"index\":%zu,\"kind\":%u,\"pc\":%u,\"address\":%u,\"width\":%u,\"value\":%u,\"write\":%s,\"accepted\":%s,\"previous\":\"%s\",\"chain\":\"%s\"}\n",
                index,unsigned(event.kind),event.pc,event.address,event.width,event.value,event.write ? "true" : "false",
                accepted ? "true" : "false",predecessor.c_str(),ledger->previous.c_str());
            require(!std::ferror(output),"audit write failure");
            if (!accepted) dispose(false,ledger->failure);
            if (ledger->complete()) dispose(true,"77 full-state observations; zero tolerated tail service");
        } catch (const std::exception& error) { dispose(false,error.what()); }
        catch (...) { dispose(false,"unknown observation failure"); }
    }
    [[noreturn]] void end() {
        const bool success=ledger && ledger->finish();
        dispose(success,ledger ? ledger->failure : "unarmed stream end");
    }
};
}
