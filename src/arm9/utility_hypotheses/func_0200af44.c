#include "contracts.h"

ba_link_hypothesis *func_0200af44(ba_link_hypothesis *entry, ba_link_hypothesis *head)
{
    ba_link_hypothesis *previous = entry->previous;
    ba_link_hypothesis *next = entry->next;
    if (previous)
        previous->next = next;
    if (next)
        next->previous = previous;
    while (head->next)
        head = head->next;
    head->next = entry;
    entry->previous = head;
    entry->next = 0;
    return entry;
}
