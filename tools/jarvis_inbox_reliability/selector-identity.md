# Inbox V1 current user DOM selector fix

Installed source changed only in `../bridge/inbox-v1/extension/chatgpt_content.js` and `../bridge/inbox-v1/tests/test_content.js`. These production files are outside this repository; `selector-identity.patch` records their exact incremental diff against the prior installed verifier, following commit 1945a1f's patch-artifact convention.

Discover current user bubbles and user-message markdown nodes first. Use the nearest `data-chatgpt-search-message-ids` ancestor's exact single UUID for baseline and post-send identity. Read canonical innerText from the unique user-message markdown node, or bubble when no markdown node exists. Do not require data-turn-key or whitespace-pre-wrap. Missing/invalid UUIDs and conflicting text representations cannot prove delivery. Retain legacy role/message-id logical-text discovery. No fallback search-unit identities are needed for the supplied DOM.

Exact canonical payload and SHA-256, consecutive stable samples, ambiguous outcome caching, idempotency and no blind resend remain unchanged. Binding, deadlines, payload, background and security behavior remain unchanged.

Validation: content 30/30; background 8/8. Includes authoritative current DOM shape with UUID, exact Markdown/Unicode payload delivery, unrelated text, missing UUID, legacy compatibility, delayed render, multiple exact identities and idempotency. Synthetic only; no browser accessed or smoke sent.

Next: reload the installed Firefox temporary add-on and the bound tab, then run the separately authorized live /chatgpt-inbox smoke. No bridge restart required.
