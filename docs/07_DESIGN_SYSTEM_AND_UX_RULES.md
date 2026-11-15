# Design System and UX Rules

**Product:** Privacy-first conversational AI  
**Version:** 1.0

## 1. Design goals

- Familiar, low-friction chat experience.
- Privacy controls are discoverable, not hidden.
- Deletion progress is understandable.
- Certificate authenticity and deletion status are not conflated.
- Calm, accessible and trustworthy visual language.
- No dark patterns around consent.

## 2. Visual direction

Use a restrained, modern interface:
- Neutral background.
- One primary accent color.
- Clear typography hierarchy.
- Subtle borders and spacing.
- Avoid excessive gradients, glass effects and animated decoration.
- Use status text plus icon; never rely on color alone.
- Keep chat readable and uncluttered.

## 3. Main navigation

- Chat
- Privacy & Data
- Deletion Requests
- Certificates
- Settings

Admin/research console must be separate and role-restricted.

## 4. Chat screen

Requirements:
- Conversation list.
- New chat.
- Message composer.
- Streaming response indicator.
- Stop generation.
- Copy response.
- Error/retry state.
- Model version disclosure in an “About this response” or settings area.
- Privacy status indicator accessible without interrupting chat.

Do not show “training enabled” as a vague badge. Explain exactly what the setting means.

## 5. Consent interaction

- Default toggle off.
- Separate from accepting terms.
- Explain data categories and purpose before enabling.
- Provide a link to full privacy details.
- Require an explicit save/confirm action.
- Show effective timestamp and policy version.
- Withdrawal should be as easy as opt-in.
- No guilt language or obstructive confirmation loops.

Suggested copy:
“Allow selected conversations to be used to improve this project's model? This is optional. If off, your conversations will not be added to model-training datasets.”

## 6. Privacy dashboard

Display:
- Training consent state.
- Consent history.
- Data categories stored.
- Data categories eligible for training.
- Number of records used in training (where safe to disclose).
- Model versions affected.
- Retention/backup policy.
- Deletion request history.

Do not reveal shard mapping or other users' metadata.

## 7. Deletion flow

Step 1: Choose scope (selected conversations or all eligible data).  
Step 2: Explain consequences and model unlearning if data was used.  
Step 3: Confirm request.  
Step 4: Show request ID and immediate exclusion status.  
Step 5: Show progress timeline.  
Step 6: Show completion certificate or explain failure.

Use clear labels:
- Request received.
- Excluded from future processing.
- Source data deletion.
- Model unlearning.
- Verification.
- Certificate issued.

Do not display “Deleted” while only tombstoning is complete.

## 8. Certificate detail page

Show:
- Certificate ID.
- Status.
- Issued date.
- Verification policy version.
- Signature status.
- Evidence policy status.
- Public key ID.
- QR code.
- Download signed certificate.
- Link to verification endpoint.

Clearly distinguish:
- “Signature authentic” from
- “Deletion checks completed”.

## 9. Public verification page

Display:
- Certificate found/not found.
- Signature valid/invalid.
- Revocation status.
- Workflow status.
- Policy version.
- Completion date.
- Scope categories checked.
- Evidence manifest digest (optional).
- Plain-language limitation statement.

Never show:
- User identity.
- Conversation content.
- Raw record IDs.
- IP address.
- Internal storage path.
- Sensitive shard assignments.

## 10. Status semantics

- Green/success: all required checks pass.
- Amber/pending: authentic request, incomplete workflow.
- Red/error: invalid, revoked or required check failed.
- Grey/unavailable: verifier cannot access authoritative status.

Always include text label and accessible description.

## 11. Accessibility

- WCAG 2.2 AA target.
- Keyboard accessible.
- Focus visible.
- Semantic headings and landmarks.
- Screen-reader labels for toggles, buttons and QR.
- Sufficient contrast.
- Reduced-motion support.
- Error messages associated with controls.
- Do not communicate status by color alone.

## 12. Responsive behavior

- Desktop: sidebar + chat area.
- Tablet: collapsible sidebar.
- Mobile: single-column chat and privacy screens.
- QR and certificate content must remain readable on small screens.
- Avoid horizontal scrolling for primary flows.

## 13. Design acceptance tests

- User can locate training consent within two interactions from chat.
- User can withdraw consent without contacting support.
- User understands tombstoned does not mean unlearning completed.
- User can see request status.
- Public verifier discloses no personal data.
- Invalid signature is visibly distinct from pending.
- Screen reader can interpret all status states.


## 14. UX requirements for transparency, race prevention and cost-aware research

### Merkle transparency log presentation
- Certificate page shows three separate checks: certificate signature, deletion evidence policy and transparency-log inclusion.
- Provide a “View inclusion proof” expandable technical section for researchers.
- Provide a plain-language explanation: “This entry is included in the platform's signed append-only log.”
- If log proof is unavailable or inconsistent, do not show an overall green/valid state.
- Do not expose private data through leaf contents or proof metadata.

### Training-job race status
- Show “Excluded from future processing” only after tombstone/epoch transaction commits.
- Show “Training job safely stopped/restarted” where a stale worker was fenced.
- Never imply that stopping a job means model unlearning completed.
- Show unlearning and verification as separate later stages.

### Cost-aware SISA research dashboard
- Provide configuration comparison for shards and slices.
- Display initial training time, deletion time, checkpoint storage, utility, forgetting and inference latency.
- Show trade-offs, not a single “best” configuration without context.
- Include hardware profile and resource-limit warning.
- Clearly label incomplete/resource-aborted experiments.
