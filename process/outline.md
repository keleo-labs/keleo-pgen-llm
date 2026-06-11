1. **Analysis:** Analyse source content, using the perspectives and topics to identify the following aspects. The objective of this phase is to organise the key elements from the source material into a methodological structure. 
  * Guide: use the `domain-framework` to identify perspectives, and sub-topics. 
  * In identifying items, determine the following:
    * **Name**
    * **Description** - short single sentence
    * **Tags** 
    * **Narrative** Succinct narrative describing the item, summarised as a bulleted list. 
    * **Further reading** avoid replicating sections of the source content, instead provide references for further reading. 
   1. **Outcomes:** What are the primary objectives of the source content, what are the intended outcomes for an organisation following this guidance?
   2. **Concerns:** Identify the primary areas of concern, what should the audience be addressing to work towards these objectives and outcomes? 
      1. **Progressive States:** For each concern how might it be assessed from an initial state to a completed state; what are the points of interest and value in the lifecycle of the concerns development? 
      2. **Work Products:** What are the work products that are produced or updated that demonstrate that concerns have achieved an identified level of progress?
         1. For each work product consider progressive levels of detail that can be used to aligned with required practice rigour and evidence of achieved level of progress. 
         2. Identify any distinct instances of identified **Work Products** that can be managed independently. 
      3. Identify any distinct instances of **Concerns** that can be progressed independently. 
   3. **Activities:** What types of work are expected to be performed, and what skills and competencies are needed to perform an activity of this kind?
      1. Consider all of the areas of concern, and their associated levels of progress, what types of work are needed to contribute towards each level of progress?
      2. Consider all of the work products that are produced, what types of work contribute to the creation and development of the work products?
      3. **Competencies:** A competency is a type of expertise, it has levels that represent increasing skill and experience. 
         1. Identify competencies needed to perform the activities. Identify the recommended competency level, by describing the required skill and experience.
      4. **Personas:** Identify `Personas` from the source content that can be used to represent a combination of **Competencies** 
      5. **Persona Groups:** Describe how `Personas` operate within teams and cross-functional groups. 
         1. For each activity, identify the *Persona Groups* that might be involved in the associated work.  
   4. **Workflows:** Identify the workflows and processes that contribute to **Outcomes**. 
      1. **Patterns:** Identify the common patterns of work, that support progression of specific aspects. 
      2. **Lifecycle:** Identify the overarching patterns of work, use the `domain-framework`'s **The Cycle** as a guide for identifying overarching patterns. 
   5. **Practices:** Use the outcomes to group the results of the analysis into separate practices, use the following heuristics:
      - **Different use-cases** (for example: greenfield vs brownfield)
      - **Different value-streams** (for example: platform building vs consuming)
      - **Different stakeholder journeys** (for example: builders vs consumers)
      - **Different capability domains** (for example: security, observability, deployment, risk, resilence)
      1. **Identify Practices:** Identify each **Practice** and its distinct objectives and outcomes. 
      2. **Identify Practice Hierarchy:** Determine the relationships between practices, and how they contribute to the broader objective of the original source content. 
      3. **Practice Concerns:** Identify the **Concerns** that contribute to this practice, the relationship should be Practice 1---* Concerns
         1. **Practice Work Products:** Identify the **Work Products** associated with the practice's **Concerns**, the relationship should be Practice 1---*Work Products
         2. **Practice Activities:** Identify the **Activities** associated with the practice's **Concerns**, the relationship should be Practice 1---*Activities
         3. **Practice Workflows:** Identify the **Workflows** associated with the practice's objectives and outcomes. 
   6. **Report:** Create a report of the the findings
2. **Mapping:** The objective of this phase is to map the methodological structure from phase 1 into a standardised format and language structure that uses an underlying baseline practice to formalise into a standardised method. 
   1. Load baseline practice and create a mapping guide based on the report generated in Step 1. 
   2. Load the `semantics.md` for rules on how to apply mapping. 
   2. If more than one practices was described, create a Method mapping to cover the overall methology presented. This should include:
      1. Method name
      2. Method description
      3. Key words
      4. Narrative explanation of the method, considering its objectives and outcomes
      5. Citation references (APA standard), to cover all references made within the method
      6. A list of all of the Practice names to include in this method
   3. For each Practice identify
      1. Practice name
      2. Practice description
      3. key words
      4. Narrative explanation of the practice, considering its objectives and outcomes
      5. Citation references (APA standard), to cover all references made within the practice
      6. **Concerns:** map the practice `Concerns` to the `Alphas` in the baseline practice, using the alpha names and description to find the most appropriate matches. 
      7. **Work Products:** map the practice Work Products to `WorkProduct` constructs
      8. **Personas and Persona Groups:** map the practice Personas to `Persona` and `PersonaGroup` constructs
      9. **Activities:** map the practice ActivitySpaces or Activities to `ActivitySpace` and/or `Activity` constructs
      10. **Patterns:** map the practice Patterns to `Pattern` and `PatternView` constructs. 
3. **JSON:** The objective of this phase is to create a machine readable representation of Phase 2 results in JSON format that precisely conforms to the provided JSON schema, has internal referential integrity and external referential integrity with the baseline practice. 
   1. Load the results from Step 2, and generate JSON file(s) to represent the results
   2. Read the `language.schema.json` to determine the JSON schema for PracticeElements: Methods, Alphas, WorkProducts, Patterns, PatternViews, Checklists, States, AlphaContributions, PracticeElementAliases, WorkProductContributions, AlphaInstanceNames,AlphaInstances,WorkProductInstanceNames, WorkProductInstances,LevelOfDetails,ActivitySpaceCore,Activity,ActivitySpace,Competency, CompetencyLevel, CompetencyLevelReference, PatternViewReference, NarrativeContext, Narratives, Persona, PersonaGroups, Focus, Citations, PracticeBaselineShape, PracticeBaseline, Practice. 
   3. Read the `semantics.md` to determine the application of the schema. 
   5. Read the `platform-adoption-kernel.json` to determine the baseline practice, and suggested narrative types. 
   6. For each practice develop a JSON representation based on the mapping that conforms to the schema, semantics, and baseline practice
   7. If a method has been identified, create a new method json, referring to the baseline practice by name, and embedded each practice. 
   8. Ensure that the final JSON documents have internal referential integrity
   9. Ensure that the final JSON documents have external baselinePractice referential integrity
   10. Ensure that the final JSON documents are fully compliant with the `languance.schema.json`
