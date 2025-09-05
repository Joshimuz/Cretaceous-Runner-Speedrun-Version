/* GTA San Andreas Custom Missions AutoSplitter (v1.0 only)
   Uses PASSED_MISSIONS counter at gta_sa.exe+0x64EC24
   Splits when the counter increases to missionNumber+1.
   Each mission split can be toggled in settings.
*/

state("gta_sa") { }

startup {
    vars.enabled = true;
    vars.memoryWatchers = new MemoryWatcherList();
	vars.lastLoad = 0;
	vars.waiting = false;

    // PASSED_MISSIONS watcher
    vars.memoryWatchers.Add(new MemoryWatcher<int>(new DeepPointer(0x64EC24)) { Name = "passedMissions" });
    vars.memoryWatchers.Add(new MemoryWatcher<int>(new DeepPointer(0x68ECF0)) { Name = "playingTime" });
	vars.memoryWatchers.Add(new MemoryWatcher<int>(new DeepPointer(0x7A67A5)) { Name = "loading" });
	
    // Mission map (targetValue = missionIndex+1, missionName)
    vars.missions = new Dictionary<int, string> {
        {1, "Introduction"},
        {2, "Childhood"},
        {3, "Catch me who can"},
        {4, "Feathers is a sign of skill"},
        {5, "New opportunities"},
        {6, "Save the Life"},
        {7, "Life's beach"},
        {8, "The Prankster"},
        {9, "6-year War"},
        {10, "Street Fighting"},
        {11, "Quieter than water"},
        {12, "The Great Cause"},
        {13, "The Big Brother"},
        {14, "July 1st"},
        {15, "In the dream"},
        {16, "Grey Hills"},
        {17, "Candyland"},
        {18, "Snowboarding"},
        {19, "The Alchemist"},
        {20, "Hello, North!"},
        {21, "Cold wind"},
        {22, "Fishing"},
        {23, "The Great Escape"},
        {24, "Nowhere to run"},
        {25, "Dangerous waters"},
        {26, "Dayargolia"},
        {27, "Oviciraptors"},
        {28, "Amarhaan"},
        {29, "Egg Stiffs"},
        {30, "The Tarbos"},
        {31, "The terrible claw"},
        {33, "Weaponwood"},
        {34, "Water patrol"},
        {35, "Cretaceous Running"},
        {36, "Dayarhell"},
        {37, "Flying school"},
        {38, "Chepei"},
        {39, "Other land"},
        {40, "Coming Home"},
        {41, "The Crocodiles"},
        {42, "Welcome to the Ghetto"},
        {43, "Death from the Sky"},
        {44, "Revenge"},
        {45, "Frontier guard"},
        {46, "Back to Alfred"},
        {47, "Mating dance"},
        {48, "I wanna bite"},
        {49, "Density Post"},
        {50, "Future depends on You"},
        {51, "Progenesis"},
        {52, "The Promenade"},
        {53, "Like a First Time"},
        {54, "Evil Return"},
        {55, "Exploration"},
        {56, "King of the Rock"},
        {57, "More than Business"},
        {58, "Fireman"},
        {59, "Grilled Chicken"},
        {60, "The new Government"},
        {61, "Freedom"}
    };

    // Add setting group
    settings.Add("splitOnMissions", true, "Split on Missions");
    settings.SetToolTip("splitOnMissions", "Enable splitting on the selected missions");

    // Add individual toggles
    foreach (var kv in vars.missions) {
        string id = "ms_" + kv.Key;
        settings.Add(id, true, kv.Value, "splitOnMissions");
    }

    vars.splitsDone = new HashSet<int>();
    vars.seenSplits = new HashSet<int>(); // Track which splits have been completed
}

init
{
	vars.enabled = true;
    vars.seenValues = new HashSet<int>();
    vars.missions = new Dictionary<int, string>();
	
    // Initialize seenSplits if not already done
    if (vars.seenSplits == null) {
        vars.seenSplits = new HashSet<int>();
    }
}

start
{
	//=============================================================================
	// Starting Timer
	//=============================================================================

	var playingTime = vars.memoryWatchers["playingTime"];

	// New Game
	//=========
	/* 
	 * The timer uses the playing time to start as soon as the game loads. 
	 */
	if (playingTime.Current > 0 && playingTime.Old == 0)
	{
        // Reset seen splits when starting a new game
        vars.seenSplits.Clear();
		return true;
	}
}

update {
    if (!vars.enabled) return;
    vars.memoryWatchers.UpdateAll(game);

    if (timer.CurrentPhase == TimerPhase.NotRunning) {
        vars.splitsDone.Clear();
        vars.seenSplits.Clear(); // Clear seen splits when timer is not running
    }
}

split {
	if (vars.memoryWatchers["loading"].Current == 1) {
		vars.DebugOutput("Loading");
		vars.lastLoad = Environment.TickCount;
		return false;
	}
	if (Environment.TickCount - vars.lastLoad < 500) {
		// Prevent splitting shortly after loading from a save, since this can
		// sometimes occur because memory values change
		if (!vars.waiting)
		{
			vars.DebugOutput("Wait..");
			vars.waiting = true;
		}
		return false;
	}
	if (vars.waiting)
	{
		vars.DebugOutput("Done waiting..");
		vars.waiting = false;
	}
	
    if (!vars.enabled) return false;

    var mw = vars.memoryWatchers["passedMissions"];
    if (mw == null) return false;

    int curr = mw.Current;
    int prev = mw.Old;

    // Only forward movement matters
    if (curr <= prev) return false;

    if (curr == 32) return false; // Weird 32nd mission which is just a cutscene without a name

    if (vars.seenSplits.Contains(curr)) return false; // Already split for this mission, don't split again

    // Check if this mission is enabled in settings
    string settingId = "ms_" + curr;
    if (!settings[settingId]) return false;
    
    // Mark this split as completed to prevent duplicate splits
    vars.seenSplits.Add(curr);
    
    return true;
}