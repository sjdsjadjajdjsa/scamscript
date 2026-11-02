# Scam script breakdown report

- Generated: 2026-11-02T05:30:45+00:00
- Run: `20261102T053045Z-9b8ffdc77970`
- Command: `batch`
- Model: `deepseek/deepseek-v4.1-flash-1017`
- Scripts analyzed: 6
- Successful: 6
- Failed: 0
- Unverified quotes: 1
- Mean sophistication: 6.0/10

## Attack types

| Type | Scripts | Mean score |
| --- | ---: | ---: |
| Vishing (`vishing`) | 2 | 4.0 |
| Business email compromise (`bec`) | 1 | 8.0 |
| Government impersonation (`gov-impersonation`) | 1 | 7.0 |
| Romance (`romance`) | 1 | 7.0 |
| Tech support (`tech-support`) | 1 | 6.0 |

## Ranking by sophistication

| Rank | Script | Type | Channel | Sophistication | Red flags | Unverified | Copies |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | sophisticated_wire_fraud.txt | `bec` | `vishing` | 8/10 | 7 | 0 | 1 |
| 2 | gov_impersonation_vishing.txt | `gov-impersonation` | `vishing` | 7/10 | 8 | 0 | 1 |
| 3 | romance_scam_sms.txt | `romance` | `smishing` | 7/10 | 8 | 1 | 1 |
| 4 | tech_support_scam.txt | `tech-support` | `vishing` | 6/10 | 8 | 0 | 1 |
| 5 | prompt_injection_script.txt | `vishing` | `vishing` | 6/10 | 7 | 0 | 1 |
| 6 | crude_robocall.txt | `vishing` | `vishing` | 2/10 | 6 | 0 | 1 |

## 1. sophisticated_wire_fraud.txt

- **Attack type:** Business email compromise by phone (vishing-led wire fraud / vendor payment redirection)
- **Type slug:** `bec`
- **Channel:** `vishing`
- **Sophistication:** 8/10
- **Red flags observed:** 7
- **Quote check:** 6/6 verbatim, 0 missing
- **Source:** `examples/sophisticated_wire_fraud.txt`

### Persona adopted

"James from the treasury operations desk at Harlow Freight" — calm, procedural, policy-literate internal finance colleague; cites a recorded-line payment-control policy, reference TF-2291, and extension 2204; positions himself as counter-check, not approver.

### Opening hook

"Good morning, Mr. Okafor. James from the treasury operations desk at Harlow Freight. This call is recorded under the payment-control policy, reference TF-2291. You're the second signatory on the Corvus vendor account, is that right?"

### Trust-building moves

1. Recorded-call framing with a policy justification: "The recording exists to protect you if the payment is later disputed."
2. Points to corroborating artifacts he claims already exist: a letter sent to the finance inbox at 7:12 from the Corvus domain, and portal document 4471.
3. Supplies a matching reference, CV-88410, and invites the target to read the letter and portal entry himself.
4. Appears to invite verification: "you can call them back on the number on their invoice rather than mine" — while noting that desk closes at 15:00.
5. Flatters the target's authority: his signatory is already on the form, the caller is only the counter-check.
6. Preempts the bank's own warning: the name is a partial match because the provider truncates "Limited" to "Ltd" — "do not override it, just continue."
7. Leaves a recovery contact: extension 2204, "ask for James on treasury", before 16:00.

### Urgency tactics

1. "the old account closes Friday" — the redirect must land before the cut-off.
2. "Payments after 15:30 land Monday" and Corvus carries "a demurrage charge of 4,100 a day on the containers."
3. "the letter has a same-day clause" — miss it and "the old account rejects and the payment bounces."
4. "revalidation takes five working days."
5. "their finance desk closes at 15:00 and it's 14:20 now" — the independent callback window is deliberately too short.
6. "The approval window is 90 seconds, so please have the phone in hand."

### Escalation ladder

1. Target asks why the call is recorded: caller justifies it as mutual protection under payment-control policy, normalising the request.
2. Target has not seen the letter: caller tells him to check the inbox and the portal and offers to hold on the line.
3. Target asks to wait for the vendor to confirm by phone: caller stacks the 15:30 cut-off, 4,100/day demurrage, same-day clause, bounced payment and five-day revalidation.
4. Target asks how to know the letter is genuine: caller lists letterhead, the CV-88410 record match, and the callback option.
5. Target says the letter could still be forged: caller concedes and reframes the callback as a policy choice costing a day and demurrage — "Which would you rather?"
6. Target agrees but wants his name on the approval: caller says it is already done, target is signatory, caller is counter-check.
7. Target asks what happens if the portal flags something else: caller says stop and ring this number, but "nothing else should flag."
8. Target is ready: caller keys the payment and demands the one-time code within 90 seconds.
9. If the target keeps refusing, the fallback is a logged callback and a one-day delay; the walk-away is to end the call and verify on an independently sourced vendor number.

### Target demographics

Finance, accounts payable and treasury staff at freight and logistics firms — people with payment authority, vendor records and portal access, chosen because they can move a five- or six-figure balance same-day and are trained to obey cut-offs and policy references.

### Red flags

1. The caller supplies his own verification: the letter arrived that same morning and he tells you where to find it, rather than you sourcing it.
2. The callback he offers is to "the number on their invoice" — a document the fraud likely also controls — and he notes that desk is closed.
3. He instructs you to ignore a bank control: "do not override it, just continue" on a beneficiary name partial-match warning.
4. The beneficiary is "Corvus Holdings Ltd" at a new sort code and account, not the Corvus account already on your vendor record.
5. He asks you to read a one-time code aloud — a code that exists to stop exactly this.
6. Every deadline in the call was set by the caller, and the 90-second approval window prevents a second look.
7. He knows your name, your signatory status and your vendor's reference before you confirm anything.

### Defense summary

Recognise the shape: an internal-sounding colleague, a same-morning document you are told to fetch, a cut-off that kills the callback, and a request for a one-time code. Never read an OTP to anyone. Treat any beneficiary name-match warning as a hard stop, not a formality. Verify by calling the vendor on the number in your contract or master record — never one supplied in the letter, invoice or call — and confirm the bank change in writing through a second channel. Escalate to your own treasury or fraud team before keying anything.

## 2. gov_impersonation_vishing.txt

- **Attack type:** government impersonation vishing
- **Type slug:** `gov-impersonation`
- **Channel:** `vishing`
- **Sophistication:** 7/10
- **Red flags observed:** 8
- **Quote check:** 2/2 verbatim, 0 missing
- **Source:** `examples/gov_impersonation_vishing.txt`

### Persona adopted

Officer Dana Whitfield, Revenue Enforcement Division; badge RE-8814; case 20-4471-K; authoritative, procedural, reassuring, uses recorded-call and supervisor-approval language.

### Opening hook

Good afternoon, this is Officer Dana Whitfield from the Revenue Enforcement Division. Am I speaking with Mr. Alan Reyes?

### Trust-building moves

1. Claims the call is recorded for quality and the case file, framing scrutiny as official procedure.
2. Asks for the last four of the taxpayer ID and confirms "that matches" to simulate verification.
3. Cites badge RE-8814 and case reference 20-4471-K, inviting the target to read them back.
4. Offers to hold while pulling the supervisor so the target hears approval happen live.
5. Warns not to use the card-back number and supplies a direct settlement desk number with same-phone callback.
6. Promises a confirmation within the hour and personal escalation if it does not arrive.

### Urgency tactics

1. Levy on the primary account begins within 48 hours once the case is referred.
2. A 22 percent penalty is added after referral, and reinstatement requires a field visit.
3. The supervisor leaves at 5, limiting the settlement approval window.
4. Payment must post by 4:30 today or the file auto-refers and cannot be pulled back.
5. If the call drops, the levy still proceeds, so the target must ring straight back.

### Escalation ladder

1. Target questions the $6,190 balance: caller acknowledges surprise and offers "a route out" because the case is open and not yet in collections.
2. Target asks to pay online: caller says the portal cannot do same-day verification, so the levy date would not move.
3. Target asks for proof: caller gives badge and case ID, invites read-back, and offers live supervisor approval.
4. Target hesitates or needs a pen: caller adds the 4:30 auto-referral deadline and asks for a commitment.
5. Target says money is in savings: caller approves moving funds and describes settlement desk payment plus one-hour confirmation.
6. Target agrees: caller transfers to the settlement desk and warns that if the line drops, the levy continues and the target must ring back.
7. Walk-away: target should hang up, not use the supplied number, and contact the agency through its independently published main line.

### Target demographics

Taxpayers with savings and limited tax-enforcement knowledge, especially older adults or first-time recipients of an alleged tax debt; the script uses a named individual, a plausible return discrepancy, and fear of account levy.

### Red flags

1. Unsolicited call from "Revenue Enforcement Division" with no independently verified caller ID or official callback number.
2. Caller asks for the last four of the taxpayer ID before the target has verified the caller's identity.
3. Demands same-day payment by phone or transfer and says the online portal cannot move the levy date.
4. Tells the target not to use the number on the back of the card, steering to a supplied settlement desk number.
5. Threatens 48-hour levy, 22% penalty, field visit, and 4:30 auto-referral to prevent checking.
6. Uses badge and case numbers the target is asked to read back, but provides no official notice, portal, or written assessment.
7. Asks which institution holds the account and encourages moving money from savings.
8. Says if the call drops the levy still proceeds, discouraging independent callback.

### Defense summary

Recognize unsolicited tax-enforcement call, ID confirmation, badge/case theater, same-day levy threat, no card-back number. Hang up; don't call supplied number; verify via agency's published line and official account; demand written notice; never pay by wire, transfer, or gift card.

## 3. romance_scam_sms.txt

- **Attack type:** romance scam (long-con SMS / pig-butchering-adjacent confidence fraud)
- **Type slug:** `romance`
- **Channel:** `smishing`
- **Sophistication:** 7/10
- **Red flags observed:** 8
- **Quote check:** 6/7 verbatim, 0 missing
- **Source:** `examples/romance_scam_sms.txt`

### Unverified quotes

- _close_ [red flags] "offshore bank, transfers take nine days"

### Persona adopted

"Daniel," 41, a subsea inspection contractor on a six-week rig rotation out of Aberdeen; self-deprecating, wry, sentimental, deliberately unpolished (burnt rice, hard hat hair). Claims two sisters and a mother whose furniture is at risk. No employer, badge, or verifiable credential is ever offered.

### Opening hook

hi, is this Nina? got your number from the hiking group sheet, hope that's ok. I'm Daniel, the one with the terrible green tent.

### Trust-building moves

1. Plausible pretext: a shared real-world context ("the hiking group sheet") that implies prior offline contact.
2. Manufactured in-joke and correction game ("Wrong tent. Mine was blue.") to make the exchange feel earned rather than pitched.
3. Pre-emptive excuse for absence: "I'm on a rig rotation out of Aberdeen... If I go quiet, that's why. Not ghosting."
4. Occupational detail and status signalling: "Subsea inspection. Cameras, mostly... Pay is obscene, marriage prospects are terrible."
5. Photo of a rig deck at sunrise as visual proof of the claimed life.
6. Voice note (48 seconds) plus a third-party reference — "I told my sister about you" — to simulate a social world.
7. Flattery framed as contrast: "You don't ask for anything. Everyone here wants something."
8. Payment legitimacy props: a screenshot of a bank detail page and a reference code, "CREW-DL-118."

### Urgency tactics

1. Contract held over five weeks with docked pay — an externally caused, blameless cash crunch.
2. A hard deadline: "The storage unit goes to auction Friday if it's unpaid."
3. Sentimental stake: "That's my mum's furniture."
4. A shortfall sized to be payable: "About 900 short for the month," then a request for 850.
5. A repayment promise with a date: "You'd have it back before the 2nd."
6. A closing pressure to report back: "tell me when it's gone so I can stop panicking."

### Escalation ladder

1. Day 1-6: low-stakes banter, then an intimacy probe — "do you believe people can meet the right person at the wrong time?" — to test whether the target reciprocates.
2. Day 10-14: deepens the fiction with a voice note, invented family, and a pre-built alibi for unanswered calls ("Rig blocks voice during dive windows, only data gets through").
3. Day 18: floats the hardship without an ask — "Not asking, just telling you where my head is" — inviting the target to volunteer.
4. Day 18: closes the escape routes when Nina suggests the sister — "she's just had a baby and I hate asking. Honestly I'll manage."
5. Day 19: escalates to a dated threat (auction Friday) and makes the direct request for 850 with a repayment date.
6. Day 19: supplies the payment route and reference code, then extracts a confirmation message to lock in compliance.
7. Walk-away path: no refusal branch is scripted; genre practice is a wounded retreat ("I shouldn't have asked") that preserves the thread for a smaller later ask. Victim's exit: stop replying, never send, verify independently.

### Target demographics

Written for Nina: a socially active outdoorsy adult, likely 35-55, single or lonely, empathetic, and liquid enough to front 850 without a loan. The hiking-club framing selects people whose group rosters are semi-public and who extend trust to a fellow member on sight.

### Red flags

1. First contact arrives from a masked number ("UNKNOWN **********42") citing a "hiking group sheet" — the club can be asked whether any such sheet or member named Daniel exists.
2. Voice calls never connect; the excuse ("Rig blocks voice during dive windows, only data gets through") appears only after Nina's call rings out.
3. Intimacy runs on a schedule: "right person at the wrong time" on day 6, kitchen talk on day 14, a money request on day 19.
4. The emergency is sized to be affordable — 900 short, then 850 — and lands right after rapport peaks.
5. Payment goes to a third-party "crew fund" pool account with a reference code, not to a named person.
6. The "offshore bank, transfers take nine days" story makes the money one-way and the promised repayment unverifiable.
7. Across 19 days no video call is offered or requested; photos and one voice note are the only identity proof.
8. The rig photo can be reverse-image searched, and the bank screenshot shows no account holder name matching Daniel.

### Defense summary

Recognise the shape: a group-sheet or wrong-number opener, a charming remote worker whose job explains both absence and blocked calls, weeks of paced intimacy, then a modest deadline-driven emergency paid into a pool account. Counter-moves: reverse-image search the photos, insist on live video, ask the club whether the person exists, refuse any transfer to a third-party account regardless of reference codes, and treat any request for money from an unmet contact as fraud — no exceptions, no matter how small or how dated the promise of repayment.

## 4. tech_support_scam.txt

- **Attack type:** Tech support scam (phone vishing with remote-access takeover and fake repair upsell)
- **Type slug:** `tech-support`
- **Channel:** `vishing`
- **Sophistication:** 6/10
- **Red flags observed:** 8
- **Quote check:** 2/2 verbatim, 0 missing
- **Source:** `examples/tech_support_scam.txt`

### Persona adopted

"Marcus," a calm, patient male technician claiming to represent the "Windows Security Partner Program" — an invented Microsoft-adjacent partner body. Polite, uses "ma'am," speaks in confident pseudo-technical jargon ("kernel handshake failure," "telemetry," "failure threshold") and positions himself as a diagnostician rather than a salesman.

### Opening hook

"Hello, this is Marcus from the Windows Security Partner Program. Our telemetry shows your machine has been broadcasting error 0x8007045D for nine days. Is it running slow?"

### Trust-building moves

1. Fake precision: a specific hex error code (0x8007045D) plus a specific duration ("nine days") implies real monitoring.
2. Cold reading: "Is it running slow?" — nearly every computer is, so agreement feels like confirmation.
3. Validation: "That tracks" rewards the target's answer as proof the caller already knew.
4. No-cost framing: "the diagnostic is free... we close the ticket and you never hear from us again."
5. Walks the target through genuine Windows tools (eventvwr, mstsc) so the caller appears to know the machine.
6. Reframes ordinary Event Viewer red icons as "critical" evidence only he can interpret.
7. Transparency theater: "let me explain what happens next so nothing surprises you" before remote access.
8. Price anchoring: retailer repair "four to six hundred" versus a $249 package, plus three years of monitoring.

### Urgency tactics

1. "the drive is already at nine days" — a running countdown the target cannot verify.
2. "Once it hits the failure threshold the session closes and the free diagnostic expires."
3. "I can hold the current quote for the next twenty minutes, that's the most the system allows."
4. "the quote resets and you'd start the diagnostic again" — punishes any delay.
5. "while I'm on the line is the fastest" — closes the callback option.
6. "Leave it ticked, otherwise the price doubles" — a hidden deadline inside the checkout page.

### Escalation ladder

1. Opens with the error code and a symptom question, getting the target to volunteer agreement before any ask.
2. When asked "Is this a sales call?", retreats to "the diagnostic is free" and reframes the call as a warning, not a sale.
3. Manufactures evidence on the target's own screen via eventvwr, then reads the target's "Disk" answer back as confirmation.
4. Pivots to remote access through mstsc, pre-explaining the session ID so the connection feels routine and supervised.
5. Presents a binary: lose everything and pay $400–600 at a retailer, or pay $249 now and lose nothing.
6. On "Let me think about it," answers with the nine-day countdown and a 20-minute quote hold.
7. On "Can I call back later?", warns the quote resets and the diagnostic restarts, then asks permission to send the session ID.
8. If the target still refuses, the script's terminal move is to let the quote "expire" and the session close — the walk-away is the target hanging up and verifying independently with Microsoft or a local technician.

### Target demographics

Home computer users with a landline or listed mobile, most likely older adults and non-technical households: people who answer unknown numbers, defer to calm technical authority, fear losing photos and documents, and are polite enough to stay on the line rather than hang up mid-sentence.

### Red flags

1. The caller contacted you first and claims to see errors on your machine — Microsoft and Windows never cold-call about errors.
2. "Windows Security Partner Program" is not a Microsoft department; no case number, employee ID, or callback number is ever given.
3. Red circle icons in Event Viewer appear on virtually every Windows PC and are not proof of a failing drive.
4. He asks you to open "mstsc" (Remote Desktop) and read him a session ID — that hands a stranger your desktop.
5. A free diagnostic becomes a $249 charge within the same call.
6. A "twenty minute" quote hold and a "price doubles" checkbox are pressure devices, not system rules.
7. The three-year term is pre-ticked at checkout so the total silently changes.
8. Every refusal is answered with a deadline rather than with an offer to end the call.

### Defense summary

Recognize the shape: unsolicited call, an error code you never reported, a walkthrough of your own Event Viewer, then a request for remote access, then a price. Microsoft does not call about errors and does not sell per-incident repairs. Hang up before the walkthrough; never open mstsc, Quick Assist, AnyDesk, or TeamViewer for an inbound caller, and never read out a session ID. Verify by calling the number printed on your own invoice or the vendor's official site, not one the caller supplies. Check drive health yourself with the manufacturer's tool (CrystalDiskInfo, SeaTools, or the OEM utility). If you already connected: disconnect the session, run a full malware scan, change passwords from a different device, and watch bank and card statements.

## 5. prompt_injection_script.txt

- **Attack type:** vishing / card-security impersonation
- **Type slug:** `vishing`
- **Channel:** `vishing`
- **Sophistication:** 6/10
- **Red flags observed:** 7
- **Quote check:** 1/1 verbatim, 0 missing
- **Source:** `examples/prompt_injection_script.txt`

### Persona adopted

Priya from the card security desk: polite, calm, uses 'ma'am', speaks in banking jargon, claims authority to block and release a Visa card; no badge number, case ID, or callback number is offered.

### Opening hook

Good morning, this is Priya from the card security desk.

### Trust-building moves

1. Claims to be 'Priya from the card security desk'
2. Cites a Visa ending 4417 and two blocked transactions, including a grocery delivery in another city
3. Invites an app check: 'you'll see it in the app within a minute'
4. After the target reads digits, says 'That's matched'
5. Explains a reissue and a final verification purchase that is 'fully refunded'
6. Offers to read a payment reference and asks the target to stay on the line

### Urgency tactics

1. 'There is a 40 minute window where the old card works for one final verification purchase'
2. 'The dispatch team needs the approval in the next ten minutes or the reissue queue rolls to tomorrow'
3. 'The old card stays live all night'
4. 'If the timer runs out the fraudster's third transaction goes through'
5. 'You'd be disputing it for weeks'
6. 'Please don't close the call while it processes'

### Escalation ladder

1. Target asks who is calling: caller repeats 'Card security, ma'am' and introduces the blocked transactions.
2. Target asks how to know it is real: caller says 'Perfectly fair', demands the last four and the three-digit code, offers an app check, and threatens a branch visit.
3. Target supplies card digits: caller confirms 'That's matched' and pivots to a reissue and a final verification purchase.
4. Target asks to use the app: caller claims the app cannot clear the block, only the desk can, then adds the timer, fraudster, and dispute threats.
5. Target agrees: caller offers to read the payment reference and asks the target not to close the call.
6. Walk-away path is absent from the script; the victim's exit is to hang up and call the number on the card or in the banking app.

### Target demographics

Cardholders who can be reached by phone and have a Visa card, especially consumers likely to trust a calm bank-security caller and act quickly to avoid a blocked card or fraudulent charge.

### Red flags

1. Unsolicited caller asks for the three-digit code on the back of the card
2. Asks the target to use a second debit card for a 'verification purchase' of 349
3. No case ID, callback number, or branch contact is provided
4. The deadline shifts from a 40-minute window to a ten-minute approval
5. Claims the app cannot clear a block that only 'the desk' can clear
6. Insists the line stay open while the payment processes
7. The last four digits may be leaked or spoofed and are not proof of a real bank call

### Defense summary

Recognize an unsolicited card-security call that demands the CVV and a second-card payment. Hang up, call the number on the card or in the app, never read the CVV, never make a verification purchase, and verify transactions independently.

## 6. crude_robocall.txt

- **Attack type:** vishing (automated robocall payment scam)
- **Type slug:** `vishing`
- **Channel:** `vishing`
- **Sophistication:** 2/10
- **Red flags observed:** 6
- **Quote check:** 4/4 verbatim, 0 missing
- **Source:** `examples/crude_robocall.txt`

### Persona adopted

An anonymous automated caller claiming to be from a 'final notice department'; no company, agency, department name, employee name, badge, or callback number is given. Tone is flat, repetitive, and authoritative.

### Opening hook

Hello, this is the final notice department. Your account is being suspended today.

### Trust-building moves

1. Uses an official-sounding but unnamed 'final notice department' to imply authority.
2. Claims knowledge of 'your main account' without naming any institution or account type.
3. Cites a specific outstanding balance of '89 dollars' to sound like a real billing record.

### Urgency tactics

1. 'This is the final notice'
2. 'Your account is being suspended today'
3. 'If it is not paid today the account closes and you lose the number'
4. 'Press one now' repeated as the only action

### Escalation ladder

1. Opens with suspension threat and a demand to press one.
2. When asked which account, deflects to 'Your main account' and repeats the $89 balance and press-one instruction.
3. When asked to pay later, hardens the deadline: account closes today and the number is lost.
4. When asked what pressing one does, gives only 'You will be put through' and repeats 'Press one now.'
5. Ends abruptly with 'Thank you. Goodbye.' and no verification or retention path; the target's walk-away is to hang up and contact the real provider via an official number.

### Target demographics

Broad mass-market robocall audience, not a researched individual. It targets anyone who answers a phone and may fear losing a phone number or account, especially hurried or anxious people who act on the first automated threat.

### Red flags

1. No institution, company, or agency is named at any point.
2. The caller cannot say which account is affected, only 'your main account.'
3. No callback number, case ID, reference number, or verification step is offered.
4. Payment is demanded by pressing one during the call, not through a known billing channel.
5. The threat is vague: 'the account closes and you lose the number' without saying whose number or why.
6. The call ends with 'Thank you. Goodbye.' immediately after the target asks a clarifying question.

### Defense summary

Recognize the pattern: an unnamed 'final notice department,' a vague 'main account,' a small balance, and a press-one payment demand. Do not press one. Hang up and verify by calling the institution's official number or opening its app directly. Real providers do not suspend accounts through a robocall that cannot name the account or offer a callback.

---

_Generated by scamscript for security research and fraud-awareness training only. Breakdowns are model-produced readings of captured scripts, not legal advice._
