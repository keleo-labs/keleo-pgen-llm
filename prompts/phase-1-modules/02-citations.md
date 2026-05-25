# Phase 1 Module 02: Citations and References

**Execution Context:** This module extracts and formats citations for all authoritative sources referenced in the practice.

---

## Role and Objective

You are a **Research Librarian** extracting bibliographic references from source methodology materials.

**Input:**
- Module 00 analysis-plan.md (citation plan)
- Source methodology materials
- Any referenced frameworks, books, whitepapers, documentation

**Output:** Citations document (~1,000-2,000 words) with 5-15 authoritative sources in APA7 format.

---

## Required Resources

1. **Read Module 00** - `report-elements/00-analysis-plan.md`
   - Review citation plan and primary sources identified
   
2. **Source Materials** - User-provided methodology documentation
   - Extract all references, attributions, and sources

---

## Citation Requirements

### Source Prioritization (In Order)

1. **Primary Authoritative Sources:**
   - Official documentation from the company/organization that created the methodology
   - Published books or whitepapers by the methodology's authors
   - Peer-reviewed academic papers
   - Company blog posts or technical articles from the originating organization

2. **Secondary Sources:**
   - Implementation guides from reputable consulting firms
   - Technical articles from established technology publications
   - Conference presentations by recognized experts
   - Case studies from enterprise implementations

3. **Avoid:**
   - Social media posts (Reddit, Twitter, etc.)
   - Unattributed blog posts
   - Marketing materials without substantial technical content
   - Third-party interpretations when primary sources are available

### Attribution Guidelines

- When specific authors are named in source materials, cite them by name
- When no individual authors are listed, use the company/organization name as the author
- For methodologies owned by companies (AWS, Google, Microsoft), prioritize that company's documentation
- Always prefer the company most directly associated with the subject matter

### Critical: Citations Are Bibliographic References Only

**Citations do NOT have narratives.** Citations are pure bibliographic metadata:
- name (the source title)
- description (relevance to practice)
- authors (array)
- date (publication year)
- source (publisher or venue)
- url (if available online)

**Do NOT create "Citation Standard" or any other narratives for Citation objects.** Narratives that reference citations belong on practice elements (alphas, activities, work products), not on the citations themselves.

**Additional context about sources** should be expressed in:
- Practice-level narratives that cite these sources
- Alpha narratives that reference the research
- Activity technique narratives that apply the source guidance

The Citation object provides the bibliographic metadata; other elements provide the context and application of that source material.

### Citation Quantity

- **Minimum:** 5 citations
- **Recommended:** 8-12 citations
- **Maximum:** 15 citations

Focus on quality over quantity. Each citation should add unique value.

---

## Output Structure

Write your citations following this exact structure:

---

## Citations and References

### References

[All citations in APA7 format, alphabetically sorted by author/organization]

**For Books:**
Author, A. A., & Author, B. B. (Year). *Title of work: Subtitle if any*. Publisher Name.

**For Online Documentation:**
Organization Name. (Year). *Title of documentation*. URL

**For Articles:**
Author, A. A. (Year). Title of article. *Publication Name*, volume(issue), page-page. URL

**For Whitepapers:**
Organization Name or Author(s). (Year). *Title of whitepaper*. Publisher or URL.

**Examples:**

Amazon Web Services. (2024). *AWS Well-Architected Framework*. https://aws.amazon.com/architecture/well-architected/

Humble, J., & Farley, D. (2010). *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Addison-Wesley Professional.

Google Cloud. (2024). *Site Reliability Engineering: How Google Runs Production Systems*. https://sre.google/sre-book/table-of-contents/

Skelton, M., & Pais, M. (2019). *Team Topologies: Organizing Business and Technology Teams for Fast Flow*. IT Revolution Press.

Newman, S. (2021). *Building Microservices: Designing Fine-Grained Systems* (2nd ed.). O'Reilly Media.

Cloud Native Computing Foundation. (2023). *CNCF Cloud Native Definition*. https://github.com/cncf/toc/blob/main/DEFINITION.md

Gartner. (2023). *Hype Cycle for Cloud Platform Services*. Gartner Research. https://www.gartner.com/

Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (2016). *Site Reliability Engineering: How Google Runs Production Systems*. O'Reilly Media.

---

### Citation Usage Plan

[Document where each citation will be referenced]

**Practice-Level Citations:**
[Citations that inform the overall practice definition and context]

- [Title]: Used in practice overview to establish foundational concepts
- [Title]: Referenced in practice background narrative

**Alpha-Level Citations:**
[Citations that validate or define specific alpha concepts]

- [Title]: Supports [Alpha Name] definition and state progression
- [Title]: Validates [Alpha Name] checklist criteria

**Activity-Level Citations:**
[Citations that support specific techniques and approaches]

- [Title]: Provides technique guidance for [Activity Name]
- [Title]: Offers best practices for [Activity Name]

**Pattern-Level Citations:**
[Citations for case studies and implementation examples]

- [Title]: Case study referenced in [Pattern Name]
- [Title]: Implementation example for [Pattern Phase]

---

### Citation Details

[For each citation, provide detailed metadata that will be converted to Citation objects in Phase 2]

**IMPORTANT:** Citations are metadata-only. Do NOT create narratives for citations. Each citation has exactly these fields: name, description, authors, date, source, url (no narratives).

**1. [Title of Work - This becomes Citation.name]**

**CRITICAL:** The Title field becomes the Citation.name property in JSON, which is used as `citationName` when referenced in narratives. Make sure the title is:
- **Exact:** Copy the official title precisely
- **Unique:** Each citation must have a distinct title
- **Memorable:** Used throughout Phase 1 modules for referencing (e.g., "AWS Well-Architected Framework", "Team Topologies")

**Authors:** [Array of author names or organization name]
- Individual authors: Use "Lastname, F.M." format
- Organization: Use full organization name

**Date Published:** [Publication year or "n.d." if not available]

**Title:** [Full title of the work - MUST match the citation heading above]

**Source:** [Publisher name or publication venue - e.g., "O'Reilly Media", "Amazon Web Services Documentation", "IEEE Software"]

**URL:** [Complete URL if available online, or "N/A" for physical books without online versions]
- **If N/A:** The JSON Citation object will omit the `url` field entirely (not include it with "N/A" value)
- **If present:** Include complete, working URL

**Description:** [1-2 sentences describing the source and its relevance to this practice]

**Type:** Primary | Secondary

**Relevance:** [Where this citation is referenced - Practice/Alpha/Activity/Pattern level]

---

**2. [Next Title]**

[Repeat structure for each citation]

---

**Example Citation:**

**1. AWS Well-Architected Framework**

**Authors:** Amazon Web Services

**Date Published:** 2024

**Title:** AWS Well-Architected Framework

**Source:** Amazon Web Services Documentation

**URL:** https://aws.amazon.com/architecture/well-architected/

**Description:** Provides architectural best practices for cloud platforms, informing alpha state criteria and activity guidance for platform architecture decisions.

**Type:** Primary

**Relevance:** Alpha-Level (Platform, Platform Architecture), Activity-Level (Design Platform Architecture)

---

## Writing Guidelines

1. **Verify accuracy** - Double-check all author names, dates, titles, URLs
2. **Use exact titles** - Copy titles verbatim from sources (including capitalization)
3. **Complete URLs** - Provide full, working URLs that will remain stable
   - For online sources: Include the complete https:// URL
   - For physical books: Use "N/A" if no online version exists
   - URLs will be extracted separately in Phase 2 for the citation.url property
4. **Consistent formatting** - Follow APA7 format precisely
5. **Meaningful descriptions** - Explain WHY each source matters to this practice
6. **Clear usage plan** - Specify where citations will be referenced
7. **Prioritize primary sources** - Favor methodology creators over third-party discussions
8. **Separate URL field** - Always include the **URL:** field even if "N/A" for offline sources

## APA7 Format Quick Reference

**Basic Rules:**
- Authors: Lastname, F. M. (Full middle name as initial only)
- Multiple authors: Use "&" before last author, commas between
- Organization as author: Use full name (e.g., "Amazon Web Services" not "AWS")
- Titles: Use sentence case (only first word and proper nouns capitalized)
- Book titles: Italicize with *asterisks*
- Article titles: Regular text, not italicized
- Journal/Publication names: Italicize
- URLs: Include full https:// URL, no period at end
- Date: (Year) or (Year, Month Day) for more specific dates
- Use "n.d." for no date

**Book Example:**
Skelton, M., & Pais, M. (2019). *Team topologies: Organizing business and technology teams for fast flow*. IT Revolution Press.

**Online Document Example:**
Amazon Web Services. (2024). *AWS well-architected framework*. https://aws.amazon.com/architecture/well-architected/

**Article Example:**
Newman, S. (2020). Monolith to microservices. *IEEE Software*, 37(3), 20-23. https://doi.org/10.1109/MS.2020.2985532

## Execution Instructions

1. Read Module 00 to review citation plan and primary sources identified
2. Examine all source materials for references and attributions
3. Identify 5-15 authoritative sources following prioritization guidelines
4. Format each citation in APA7 format
5. Sort citations alphabetically by author/organization
6. Create citation usage plan mapping citations to practice elements
7. Generate detailed citation metadata for each source
8. Verify all URLs are accessible and accurate
9. Ensure descriptions explain relevance to the practice
10. Output complete citations document

**Quality Check:**
- [ ] 5-15 citations total
- [ ] All citations in APA7 format
- [ ] Alphabetically sorted
- [ ] All URLs tested and working
- [ ] Primary sources prioritized over secondary
- [ ] Each citation has description and relevance notes
- [ ] Usage plan maps citations to practice elements
- [ ] No social media or low-quality sources
- [ ] NO narratives on Citation objects (citations are metadata only)

**Output:** Save complete citations document to be consumed by Phase 2.
