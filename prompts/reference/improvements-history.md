1. if the plan needs to compact during its run, then it is important that after compaction, it reloads key information
   1. The element names from platform-adoption-kernel.json - the baseline practice. The reports generated MUST accurately refer to its elements
   2. The language.schema.json - it is imperative that before any JSON is created that the schema is reloaded and used programmatically
2. The final method report can result in a single massive file. To avoid this being a potential issue, break the report into overall method & commentary, and an included practices. 
3. During planning if any module appears that it may create a very large file, break this into subparts, for example, one part for each focus. 
4. In phase 2, a single method JSON with embedded practices may result in a very large file. To avoid this, create the method JSON with practiceNames instead of embedded practices, and create separate practice JSON files for each practice. 
   1. iterate through each practice by practice. Only load the necessary content for that specific practice to reduce overhead. 
      1. given the potential sizes of practices, develop their content incrementally based on the module reports, on a module, by module basis. 
      2. when all modules have been processed, review and update the practice for referential integrity
   2. When all practices have been complete, do a final integrity pass through all generated content
5. I've added a url property to the Citation schema, accommodate this in JSON creation. 
6. create subagents to operate the plans across practices concurrently
7. The original prompts were created to be used with Gemini, however, this is no longer the case. Refactor and remove references to gemini, the skill should use the most appopriate models for the task at hand. 
8. you've created a number of python modules to support the process. Organise these into a `utils` folder, and incorporate its use within the plan. 
9. Allow the user to start a new session by picking up results from a historical session, referring to a directory with that sessions work in progress. The plan should review what had been completed so far, and then develop a plan to complete the skill's objectives based on this material. 