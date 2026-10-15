#pragma once
#include "prefix.h"

namespace task_aw6 {
class Controller {
    FILE* output=nullptr;
    task_aw2::PassiveSource source=nullptr;
    std::unique_ptr<Ledger> ledger;
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
public:
    void start(FILE* file,task_aw2::PassiveSource passive) {
        output=file; source=passive;
        try {
            require(output && source,"capture/audit ownership");
            const auto observed=source();
            task_aw2::audit_snapshot(output,observed);
            ledger=std::make_unique<Ledger>(observed);
            require(source()==observed,"entry changed before binding");
            std::fprintf(output,"{\"event\":\"entry\",\"sha256\":\"%s\",\"events\":69}\n",task_aw2::digest(observed).c_str());
        } catch (const std::exception& error) { dispose(false,error.what()); }
        catch (...) { dispose(false,"binding exception"); }
    }
    void observe(Kind kind,uint32_t pc,uint32_t address=0,uint32_t width=0,uint32_t value=0,bool write=false) {
        try {
            require(ledger && source,"unarmed reduced controller");
            Observation actual{kind,pc,address,width,value,write,source()};
            task_aw2::audit_snapshot(output,actual.state);
            const auto predecessor=ledger->previous;
            const auto index=ledger->cursor;
            const bool accepted=ledger->accept(actual,predecessor);
            std::fprintf(output,"{\"event\":\"observation\",\"index\":%zu,\"kind\":%u,\"pc\":%u,\"address\":%u,\"width\":%u,\"value\":%u,\"write\":%s,\"accepted\":%s,\"previous\":\"%s\",\"chain\":\"%s\"}\n",
                index,unsigned(kind),pc,address,width,value,write ? "true" : "false",accepted ? "true" : "false",predecessor.c_str(),ledger->previous.c_str());
            require(!std::ferror(output),"audit write");
            if (!accepted) dispose(false,ledger->failure);
            if (ledger->complete()) dispose(true,"11 instructions/69 observations; before status fetch and all scheduler tails");
        } catch (const std::exception& error) { dispose(false,error.what()); }
        catch (...) { dispose(false,"reduced observation exception"); }
    }
    [[noreturn]] void end() { dispose(false,"missing reduced-prefix event"); }
};
}
