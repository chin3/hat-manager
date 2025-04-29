flowchart TD
  Start["🎯 Mission Start (Goal Given)"]
  BuildTeam["🧢 Assemble Hats (Storyteller, Critic)"]
  Storyteller["📜 Storyteller Generates Output"]
  Critic["🧑‍⚖️ Critic Reviews Output"]
  RevisionNeeded{❓ Revision Needed?}
  Retry["🔄 Storyteller Retries Based on Feedback"]
  Approve["✅ Critic Approves"]
  Debrief["📜 Generate Mission Debrief"]
  Awards["🏆 Agent Awards Ceremony"]
  Reflections["🎤 Final Agent Reflections"]
  Archive["🗂️ Save Mission Archive (with Reflections)"]
  End["🏁 Mission Complete"]

  Start --> BuildTeam
  BuildTeam --> Storyteller
  Storyteller --> Critic
  Critic --> RevisionNeeded
  RevisionNeeded -- Yes --> Retry
  Retry --> Critic
  RevisionNeeded -- No --> Approve
  Approve --> Debrief
  Debrief --> Awards
  Awards --> Reflections
  Reflections --> Archive
  Archive --> End



  mini QA Loop flowchart
  flowchart TD
  StartQA["📜 Storyteller Output"]
  CriticQA["🧑‍⚖️ Critic Reviews"]
  RevisionNeededQA{❓ Revision Required?}
  RetryQA["🔄 Storyteller Retries"]
  ReCriticQA["🧑‍⚖️ Critic Re-Reviews"]
  ApprovedQA["✅ Critic Approves"]
  ManualReviewQA["👤 Manual User Review (Approve/Retry)"]

  StartQA --> CriticQA
  CriticQA --> RevisionNeededQA
  RevisionNeededQA -- Yes --> RetryQA
  RetryQA --> ReCriticQA
  ReCriticQA --> RevisionNeededQA
  RevisionNeededQA -- No --> ApprovedQA
  RevisionNeededQA -- No Tag/Error --> ManualReviewQA
  