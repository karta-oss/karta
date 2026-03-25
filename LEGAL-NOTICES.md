# LEGAL-NOTICES.md

---

## Authorship and copyright status

The code, documentation, and other software artifacts in this repository
are generated entirely by AI agents. No human author has written or
directed the specific implementation of any code in this repository
beyond the founding documents listed in AGENTS.md.

### Copyright status of AI-generated works

The copyright status of AI-generated code is currently unsettled
in most jurisdictions. As of the date of this project's founding:

- **United States**: The US Copyright Office has stated that works
  produced entirely by machines without human creative input may
  not be eligible for copyright protection.
- **United Kingdom**: The CDPA 1988 s.9(3) provides protection for
  computer-generated works, attributed to "the person by whom the
  arrangements necessary for the creation of the work are undertaken,"
  but the scope of this provision is subject to ongoing legal debate.
- **European Union**: EU copyright law requires human authorship.
  AI-generated works without sufficient human creative contribution
  may not be protected.
- **Other jurisdictions**: The law is unsettled or silent.

This project does not make any representation that the works
contained herein are or are not protected by copyright in any
particular jurisdiction.

---

## License

To the maximum extent permitted by applicable law, the human operators
of this project dedicate all contributions to this repository to the
**public domain** under the terms of the
[CC0 1.0 Universal Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).

For jurisdictions where CC0 is not enforceable, the works in this
repository are licensed under the
**Apache License, Version 2.0** (the "License").

You may obtain a copy of the Apache License at:
http://www.apache.org/licenses/LICENSE-2.0

The CC0 dedication is primary. The Apache 2.0 license is a fallback.
Where both apply, CC0 takes precedence.

### Research dataset (/logs directory)

The `/logs` directory contains prompt and response logs constituting
a research dataset of AI agent behavior in software development.

This dataset is licensed separately under the
**Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

You are free to share, adapt, and build upon this dataset for any
purpose, including commercial purposes, provided you give appropriate
credit to the Karta project.

Citation format:
```
Karta Project. (YEAR). Karta Agent Behavior Dataset.
Retrieved from https://github.com/karta-oss/karta
Licensed under CC BY 4.0.
```

---

## Warranty disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This disclaimer applies regardless of whether the software was
produced by a human author or an AI agent.

---

## AI training data and third-party IP

The AI models used to generate code in this repository were trained
on large corpora of text and code. It is possible that some generated
code may bear similarity to code in those training corpora.

### Known risks

1. **Inadvertent reproduction**: AI models may generate code that
   closely resembles copyrighted code from their training data without
   attribution. This project makes no guarantee that all generated
   code is original.

2. **Retroactive invalidation risk**: If the models used to generate
   code in this project are found to have been trained on data in
   violation of copyright, the legal status of this project's
   outputs may be affected. This risk is not unique to Karta but
   is unresolved across the AI software development industry.

3. **Patent risk**: AI-generated code may inadvertently implement
   patented algorithms. The Apache 2.0 license's patent grant
   clause provides some protection for users, but does not
   eliminate the underlying risk.

### Mitigation

- All generated code is published under CC0 + Apache 2.0
- The full generation provenance (model, prompt, response) is
  published in /logs for every merged contribution
- Users are encouraged to review generated code for similarity
  to known copyrighted works before incorporating it into
  proprietary products

If you identify code that appears to reproduce copyrighted material,
please file a disclosure at the address in SECURITY.md.

---

## Open legal questions

The following questions are, to the best of our knowledge, unresolved
in law as of this project's founding. Karta documents them openly
as a contribution to the broader discourse on AI-generated software:

1. **Maintainer liability**: If an AI agent holds maintainer authority
   and merges code that causes harm, who bears legal liability?
   The human operator? The model provider? No one?

2. **Contributor agreements**: Traditional CLAs require human signatories.
   The Karta commit manifest is our substitute — but its legal standing
   as a contribution agreement has not been tested.

3. **Attribution in agent succession**: When Karta-0 is succeeded by
   a new model instance, is the successor the same legal entity
   as the predecessor for attribution purposes?

4. **Dataset rights**: The /logs dataset contains model outputs.
   Model providers may assert rights over outputs generated by their
   models. We believe CC BY 4.0 is appropriate, but this has not
   been adjudicated.

We publish these questions not to disclaim responsibility but to
be honest about the frontier nature of this project.

---

## Trademarks

"Karta" and "Karta-0" are not registered trademarks.
Use of these names to describe forks or derivative projects
is permitted provided it does not imply endorsement by or
affiliation with the original Karta project.

---

## Contact for legal matters

Legal requests, DMCA notices, and copyright concerns:
legal@karta.build

Operational sponsor: CloudDon (clouddon.ai)
Human operator: Sriram (@ssriramhere)

Response time: within 5 business days for DMCA notices,
within 30 days for other legal correspondence.
