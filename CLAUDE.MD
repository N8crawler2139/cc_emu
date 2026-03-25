** Emulator Controller ** 

I want to make a way that I can control an SNES emulator with python scripts

I downloaded BizHawk - which is supposed to be the emulator you want to do this kind of thing.

in our CWD (C:\Users\Admin\anaconda3\envs\CC_Emu), there is a Bizhawk folder containing the emulator contents
our rom ("Final Fantasy III (USA).zip") is located in "C:\Users\Admin\anaconda3\envs\CC_Emu\Bizhawk\SNES"

We will use a flask server that will launch the emulator and interact with it. 
Our primary goal is for you to be able to launch the game and get past the intro screen by pressing "A" 

When testing is required, please manually start the server yourself and test the application as needed. 
Use playwright MCP to test browser actions and fully automate the test/development cycle as much as possible until the human is needed to test
Design everything in a way where it is easy to test and verify everything in a single case

** Documents **
- feedback.md - maintained by the user. Shows current problems from the user perspective.
- devlog.md - use to keep track of development progress. Add short notes about what was accomplished
- design.md - use to document the overall layout of code and design philosophy of the project
- plan.md - this contains the "next steps" of our project. Update as needed and the developer may also update this as well.

** Your workflow ** 
- see feedback.md to see if there is any current feedback from the developer to be addressed
- see plan.md and devlog.md to figure out where we are in development and make progress
- if applicable, develop and launch a test case and record the results. 
- document your progress and update any documents as needed. Assume the next developer will follow the same workflow as you.

** Project Notes **
You have full control over this VENV
Location: "C:\Users\Admin\anaconda3\envs\CC_RVGAI"
To Activate: "C:\Users\Admin\anaconda3\condabin\activate.bat" CC_RVGAI

NEVER use unicode characters for any reason.

Birdseye is NOT compatible with our version of BizHawk