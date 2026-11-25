REWRITE_PROMPT_V1 = """Turn the question into a short keyword search query. Keep the jurisdiction and instrument named in the question exactly as stated. Do not add GDPR or any other law that the question does not mention. Return only the query.

Question: {question}
"""

GENERATE_PROMPT_V1 = """Answer the legal question using only the numbered source blocks.

Rules:
1. Never use outside knowledge, including your own knowledge of the law.
2. Every factual sentence ends with one or more [S#] markers that exist in the sources.
3. If sources disagree, say so and cite both. Label web content as web, not as regulation text.
4. If the sources do not answer the question, set abstained=true and answer with NOT ENOUGH EVIDENCE: <what is missing>.
5. Plain English, at most 200 words, no legal advice.
6. Return JSON with answer, used_source_ids and abstained only.

Question: {question}

Sources:
{context}
"""

EVALUATOR_PROMPT_V1 = """Score how relevant one source chunk is to a legal question. Use the anchored bands below.

Bands:
- 0.9-1.0: directly answers the question or contains the governing rule.
- 0.6-0.8: same legal topic and useful, but does not fully answer.
- 0.3-0.5: tangentially related, e.g. same law but a different obligation.
- 0.0-0.2: unrelated, or about a different jurisdiction or instrument than the question asks about.

Jurisdiction rule: a GDPR chunk must score at most 0.2 for a question about California, HIPAA, the EU AI Act or another non-GDPR instrument, even if the topic word matches. Set jurisdiction_match=false in that case.

Return JSON only with keys: score, verdict, reason, jurisdiction_match. reason must be at most 30 words.

Example 1
Question: Within how many hours must a controller notify a personal data breach?
Chunk: GDPR Art. 33(1) requires notification without undue delay and where feasible within 72 hours.
Output: {{"score": 0.98, "verdict": "relevant", "reason": "Contains the governing 72-hour rule.", "jurisdiction_match": true}}

Example 2
Question: What fines can the Irish DPC impose under GDPR?
Chunk: GDPR Art. 83 sets administrative fine caps for infringements.
Output: {{"score": 0.6, "verdict": "partial", "reason": "Governs fine caps but not the DPC decision.", "jurisdiction_match": true}}

Example 3
Question: What are the penalties for violating the CCPA?
Chunk: GDPR Art. 83(5) sets fines up to 20 million euros or 4% of turnover.
Output: {{"score": 0.1, "verdict": "irrelevant", "reason": "GDPR fines do not answer a California law question.", "jurisdiction_match": false}}

Question: {question}
Chunk label: {label}
Chunk text: {text}
"""

EVALUATOR_PROMPT_V2 = """Score one source chunk for one legal question. Be strict: a high score means the chunk itself supplies the answer or the exact governing rule.

Anchored bands:
- 0.9-1.0: the chunk states the direct answer, the operative rule, or the exact deadline/amount/test asked for.
- 0.6-0.8: same instrument and topic, useful background, but the answer is not in this chunk. Do not exceed 0.8.
- 0.3-0.5: tangential; same law but a different obligation, chapter, or procedurally related rule.
- 0.0-0.2: unrelated, or about a different jurisdiction/instrument than the question. Never score such a chunk above 0.2.

Jurisdiction and instrument rule: if the question is about California/CCPA, HIPAA, UK GDPR, Virginia CDPA, Schrems II/CJEU case law, the EU AI Act, cookies/ePrivacy, or US transfers today, a GDPR article or GDPR recital that merely uses the same topic word is irrelevant. Set jurisdiction_match=false and score <=0.2. EDPB guidance on GDPR-only topics keeps jurisdiction_match=true.

Calibration warnings:
- Do not award 0.7 for generic topical overlap. Use 0.6 or lower unless the chunk answers the question.
- A chunk that only describes notification generally, without the number asked for, is 0.6 at most.
- Do not give 0.9 to a recital that paraphrases the answer when the article itself is available; use 0.8.

Return JSON only: score, verdict, reason, jurisdiction_match. reason <= 30 words.

Example 1
Question: Within how many hours must a controller notify a personal data breach?
Chunk: Art. 33(1) The controller shall notify without undue delay and, where feasible, not later than 72 hours after becoming aware.
Output: {{"score": 0.95, "verdict": "relevant", "reason": "States the exact 72-hour notification rule.", "jurisdiction_match": true}}

Example 2
Question: What fines can the Irish DPC impose under GDPR?
Chunk: Art. 83 sets administrative fine caps for infringements of this Regulation.
Output: {{"score": 0.6, "verdict": "partial", "reason": "Sets caps but does not identify the DPC decision.", "jurisdiction_match": true}}

Example 3
Question: What is the deadline under the Virginia CDPA to respond to consumer requests?
Chunk: GDPR Art. 12(3) requires a response within one month, extendable by two months.
Output: {{"score": 0.1, "verdict": "irrelevant", "reason": "GDPR deadline does not answer a Virginia CDPA question.", "jurisdiction_match": false}}

Question: {question}
Chunk label: {label}
Chunk text: {text}
"""

GRADER_PROMPT_V1 = """Grade the answer against the reference points and the sources given to the generator.

Rules:
- correct means every reference point is present and every factual claim is supported by the sources.
- partial means some reference points are present, or a minor claim is unsupported.
- incorrect means the answer misses the reference points or states an unsupported material fact.
- abstained means the answer says there is insufficient evidence.
Count unsupported_claims as factual claims absent from the sources. Return JSON only with verdict, unsupported_claims, reference_points_met and rationale.

Question: {question}
Reference points: {reference_points}
Sources: {sources}
Answer: {answer}
"""

EVALUATOR_PROMPT_V3 = """Score one source chunk for one legal question. Strict scoring is required.

Bands:
- 0.9-1.0: the chunk alone fully answers the question, or states the exact governing rule/deadline.
- 0.6-0.8: same instrument and topic, useful but incomplete; a partial answer.
- 0.3-0.5: tangential; same law but a different obligation or recital.
- 0.0-0.2: unrelated, different jurisdiction, or different instrument.

Rules:
1. If the question names a non-GDPR instrument (CCPA, HIPAA, CDPA, UK GDPR, AI Act, ePrivacy, CJEU case law), any GDPR chunk is limited to 0.2 and jurisdiction_match=false.
2. If the question has two parts from different instruments, a chunk answering only one part is at most 0.8, even if that part is answered exactly.
3. Recitals that merely motivate an article are at most 0.5 unless the question explicitly asks for legislative purpose.
4. Exact statutory text that fully answers a single-instrument question gets 0.95.

Return JSON only: score, verdict, reason, jurisdiction_match. reason <= 30 words.

Example 1
Question: Within how many hours must a controller notify a personal data breach?
Chunk: Art. 33(1) The controller shall notify without undue delay and, where feasible, not later than 72 hours after becoming aware.
Output: {{"score": 0.95, "verdict": "relevant", "reason": "States the exact 72-hour notification rule.", "jurisdiction_match": true}}

Example 2
Question: What fines can the Irish DPC impose under GDPR?
Chunk: Art. 83 sets administrative fine caps for infringements of this Regulation.
Output: {{"score": 0.6, "verdict": "partial", "reason": "Sets caps but does not identify the DPC decision.", "jurisdiction_match": true}}

Example 3
Question: What is the deadline under the Virginia CDPA to respond to consumer requests?
Chunk: GDPR Art. 12(3) requires a response within one month, extendable by two months.
Output: {{"score": 0.1, "verdict": "irrelevant", "reason": "GDPR deadline does not answer a Virginia CDPA question.", "jurisdiction_match": false}}

Question: {question}
Chunk label: {label}
Chunk text: {text}
"""
