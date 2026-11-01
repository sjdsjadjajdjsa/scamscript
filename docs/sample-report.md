# Scam script breakdown report

- Generated: 2026-11-01T22:43:54+00:00
- Run: `20261101T224254Z-435a0e219e61`
- Command: `batch`
- Model: `deepseek/deepseek-v4.1-flash-1017`
- Scripts analyzed: 3
- Successful: 3
- Failed: 0
- Mean sophistication: 6.3/10

## Ranking by sophistication

| Rank | Script | Attack type | Sophistication | Red flags |
| ---: | --- | --- | ---: | ---: |
| 1 | gov_impersonation_vishing.txt | Government impersonation vishing (tax/revenue enforcement), ending in a controlled transfer to a fake settlement desk | 7/10 | 8 |
| 2 | romance_scam_sms.txt | romance scam / smishing long con | 6/10 | 7 |
| 3 | tech_support_scam.txt | tech support scam | 6/10 | 7 |

## 1. gov_impersonation_vishing.txt

- **Attack type:** Government impersonation vishing (tax/revenue enforcement), ending in a controlled transfer to a fake settlement desk
- **Sophistication:** 7/10
- **Red flags observed:** 8
- **Source:** `/home/cj/Projects/scamscript/examples/gov_impersonation_vishing.txt`

### Persona adopted

Officer Dana Whitfield of the "Revenue Enforcement Division," badge RE-8814, case 20-4471-K. Bureaucratic, calm, procedural tone; announces the call is recorded "for quality and for the case file" and speaks in assessment, penalty, and referral jargon.

### Opening hook

Good afternoon, this is Officer Dana Whitfield from the Revenue Enforcement Division. Am I speaking with Mr. Alan Reyes?

### Trust-building moves

1. Recorded-line claim: "this call is recorded for quality and for the case file," borrowing official-call framing.
2. Asks for the last four of the taxpayer ID, then says "that matches" so the victim's own answer becomes the proof.
3. Itemized arithmetic: a $2,840 withholding credit "never verified" producing a $6,190 balance of principal, penalties, and interest.
4. Read-back credentials: badge RE-8814 and case reference 20-4471-K, offered as checkable but never independently checkable.
5. Offers to hold while pulling the supervisor so the victim hears "the approval happen live."
6. Pre-empts callbacks by supplying a "direct settlement desk number" and asking the victim to dial from the same phone.

### Urgency tactics

1. "Once it is referred, the levy on your primary account begins within 48 hours and a 22 percent penalty is added."
2. "After that, reinstatement requires a field visit."
3. "My supervisor has to approve anything below the assessed amount, and she leaves at 5."
4. "If a payment is not posted by 4:30 today the file auto-refers, and I can't pull it back."
5. "If it drops, the levy is still going ahead, so ring straight back."

### Escalation ladder

1. Opens with name and division, then immediately demands the last four of the taxpayer ID to establish a verification ritual.
2. When the target protests never owing anything, concedes gently and reframes: "there is a route out of this," case "not referred to collections yet."
3. When the target asks to pay online, blocks the official channel: the portal "does not accept same-day verification, so the levy date would not move."
4. When the target asks what is needed, first tests liquidity: "Which institution holds the account you'd use?"
5. When the target asks how to know the caller is real, supplies badge and case number and offers live supervisor approval.
6. When the target stalls for a pen, says "Take your time" then re-imposes the 4:30 deadline and demands "Do we have a commitment?"
7. When the target says money must come from savings, reassures and offers immediate transfer to the settlement desk.
8. No refusal branch exists; terminal move is the transfer plus the drop-call trap. Walk-away: hang up, then verify through the agency's published number or written notice.

### Target demographics

A taxpayer with a filed 2023 return, a primary bank account, and savings able to cover roughly $6,190. Chosen for tax-compliance reflex and levy fear; the script probes account access early to confirm the money is reachable before investing more time.

### Red flags

1. Unsolicited call asserting a tax debt and a case number before any written notice, letter, or portal message has arrived.
2. The caller asks you to confirm the last four of your taxpayer ID, then treats your own answer as proof of their identity.
3. You are told not to use the number on the back of your card because it "routes to the retail line, not enforcement."
4. The caller asks which bank holds your account before describing any legitimate payment method.
5. You are told the official online portal cannot handle same-day verification, steering you off the real channel.
6. Badge RE-8814 and case 20-4471-K are only read back to you; nothing is offered that you could verify independently.
7. Deadlines stack within one call: 48-hour levy, supervisor leaves at 5, payment by 4:30, automatic referral if missed.
8. You are warned that a dropped call does not stop the levy, which pre-empts the natural instinct to hang up and check.

### Defense summary

Real tax agencies do not open with a balance, demand same-day payment, or route you to a "settlement desk" by transfer. Recognize the pattern: your own ID digits used as proof, the official portal declared unusable, a bank-account question before any paperwork, and stacked same-day deadlines. Counter-move: hang up mid-sentence, do not redial the number given, and contact the agency through its published number or your online account. Ask for the notice in writing; a genuine case survives a callback tomorrow.

## 2. romance_scam_sms.txt

- **Attack type:** romance scam / smishing long con
- **Sophistication:** 6/10
- **Red flags observed:** 7
- **Source:** `/home/cj/Projects/scamscript/examples/romance_scam_sms.txt`

### Persona adopted

Daniel, a 41-year-old subsea inspection worker on an Aberdeen rig; warm, self-deprecating, lonely but successful, with two sisters and odd satellite-wifi hours.

### Opening hook

hi, is this Nina? got your number from the hiking group sheet, hope that's ok. I'm Daniel, the one with the terrible green tent.

### Trust-building moves

1. Claims he got her number from a hiking group sheet and references 'terrible green tent' to seem like a real acquaintance; adapts when corrected to blue tent.
2. Self-deprecating stove/rice/pot confession and humour lower guard before any request.
3. Explains odd phone hours with a six-week Aberdeen rig rotation: 'If I go quiet, that's why. Not ghosting.'
4. Builds occupational credibility: subsea inspection, cameras, diving, 'pay is obscene'.
5. Sends a rig-deck sunrise photo and later a 48-second voice note with sensory detail 'windy'.
6. Mentions telling his sister about Nina and future kitchen planning, signalling commitment.
7. Praises her for not asking for anything and frames himself as pursued, not pursuer.
8. Uses 'Not asking, just telling you where my head is' to disclose money trouble, then asks next day.

### Urgency tactics

1. Contract held over another five weeks and pay docked for delay; cash flow is tight.
2. Storage unit goes to auction Friday if unpaid; contents are his mum's furniture.
3. Bank is offshore and transfers take nine days, so money is 'useless right now'.
4. Requests 850 and promises repayment before the 2nd; asks confirmation 'so I can stop panicking'.
5. Payment reference CREW-DL-118 is required or funds get lost in the pool account.

### Escalation ladder

1. Opens with a plausible group-sheet pretext and lets Nina correct a detail; uses the correction to continue banter.
2. Over days builds routine, photos, voice note and future talk; no money request until day 18.
3. When Nina asks how tight, gives 'About 900 short' but says 'Not asking, just telling'.
4. When Nina suggests his sister, blocks that route: new baby, hates asking, 'Honestly I'll manage'.
5. Next day escalates to direct ask: storage auction Friday, requests 850, promises repayment.
6. Sends account screenshot and reference code; asks her to mark payment and confirm immediately.
7. If she hesitates or refuses, likely practice is guilt and soft withdrawal ('I'll manage') plus a later emergency ask; victim walk-away is no payment, stop replying, preserve messages, report.

### Target demographics

Written for socially active but possibly lonely women like Nina, met through hobby or community groups, who value kindness and can front hundreds rather than thousands.

### Red flags

1. Unsolicited first text claims a shared hiking group sheet; the wrong-tent detail is corrected by Nina, showing he did not know her well.
2. Voice calls are repeatedly impossible ('rig blocks voice during dive windows'), steering all contact to text.
3. Offshore bank cannot transfer for nine days, a common excuse for why he cannot access his own money.
4. After 18 days of intimacy, a sudden emergency asks for 850 to a 'crew fund' pool account with reference CREW-DL-118.
5. Payment instructions arrive as a screenshot of a bank detail page and a reference code, not a verifiable named account.
6. Deadline is an auction Friday involving 'mum's furniture'—emotional collateral plus time pressure.
7. He discloses being 'About 900 short' then says 'Not asking' before asking the next day.

### Defense summary

Slow-burn romance scam: pretext contact, daily rapport, photos/voice, blocked live calls, then time-boxed emergency payment to a pool account. Counter: demand live video, reverse-image-search photos, never pay, preserve messages, report to bank, platform and fraud police.

## 3. tech_support_scam.txt

- **Attack type:** tech support scam
- **Sophistication:** 6/10
- **Red flags observed:** 7
- **Source:** `/home/cj/Projects/scamscript/examples/tech_support_scam.txt`

### Persona adopted

Marcus, a calm male support agent from the invented Windows Security Partner Program; claims telemetry access and diagnostic authority, uses technical jargon and a reassuring, non-sales tone.

### Opening hook

Hello, this is Marcus from the Windows Security Partner Program. Our telemetry shows your machine has been broadcasting error 0x8007045D for nine days. Is it running slow?

### Trust-building moves

1. Claims employer 'Windows Security Partner Program' and telemetry visibility.
2. Cites specific error 0x8007045D and nine-day duration.
3. Uses jargon 'kernel handshake failure' and a drive-failure narrative.
4. Says the diagnostic is free and no sale if nothing is found.
5. Walks target through Event Viewer to create participation and proof.
6. Interprets normal red Event Viewer entries as critical.
7. Introduces remote tool mstsc and explains session ID process.
8. Anchors $249 against $400-$600 retailer repair and includes three-year monitoring.

### Urgency tactics

1. Nine days of error broadcasting; drive is a countdown.
2. Free diagnostic expires once failure threshold hits.
3. Holds quote for only twenty minutes.
4. Callback resets quote and restarts diagnostic.
5. Checkbox for three-year term: leave ticked or price doubles.

### Escalation ladder

1. Open with slow-machine question and claimed telemetry error.
2. If target asks if it is a sales call, say diagnostic is free and ticket closes if clean.
3. If target agrees, direct them into Event Viewer and read back a red error.
4. If target asks what happens next, explain remote session via mstsc and session ID.
5. If target asks what if scan fails, present $249 recovery package against $400-$600 retailer cost.
6. If target says they will think about it, impose twenty-minute quote hold and expiring diagnostic.
7. If target asks to call back, say quote resets and diagnostic restarts.
8. If target accepts, send session ID and instruct them to leave three-year checkbox ticked.
9. Walk-away path: if target refuses remote access or payment, script has no further move; hang up and verify through independently found official support.

### Target demographics

Home computer users who can follow Windows commands but cannot interpret Event Viewer, especially cost-sensitive or less technical people worried about data loss and authority.

### Red flags

1. Unsolicited caller claims telemetry from your PC though you never reported an error.
2. Brand 'Windows Security Partner Program' is not Microsoft Support.
3. Asks you to open Event Viewer and treats ordinary red error icons as proof of drive failure.
4. Directs you to launch mstsc/Remote Desktop and accept a session ID.
5. Offers a 20-minute quote hold and says free diagnostic expires.
6. Says leaving a three-year checkbox ticked prevents price doubling.
7. No verifiable callback number or case ID is provided.

### Defense summary

No legitimate Microsoft agent calls about telemetry. Never open mstsc or grant remote access. Event Viewer red entries are common. Hang up, verify via official Microsoft or device-maker support found independently, and ignore quote deadlines.

---

_Generated by scamscript for security research and fraud-awareness training only. Breakdowns are model-produced readings of captured scripts, not legal advice._
