#include <plugin.h>
#include <CMessages.h>
#include "CHud.h"

using namespace plugin;

// Toggle flag
static bool gHoldToSprint = true;

// Hook for CPad::SprintJustDown
bool __fastcall SprintJustDownHook(CPad* pad) {

	static unsigned int lastkeypressed = 0;
    // Toggle with F8
    if (KeyPressed(VK_F8) && CTimer::m_snTimeInMilliseconds - lastkeypressed > 500) {
		lastkeypressed = CTimer::m_snTimeInMilliseconds;
        gHoldToSprint = !gHoldToSprint;
		CHud::SetHelpMessage(gHoldToSprint ? "FullSprint: ~g~Enabled~w~" : "FullSprint: ~r~Disabled~w~", true, false, false);
    }

    // If feature disabled, call original function
    if (!gHoldToSprint) {
        static auto original = (bool(__thiscall*)(CPad*))0x5407F0;
        return original(pad);
    }

    // --- Custom sprint logic ---
    // If the run key (SPACE) is currently held, we make the game think it is tapped.
    if (pad->GetSprint()) {
        return true; // Force sprint
    }

    // Otherwise, fall back to normal sprint logic
    static auto original = (bool(__thiscall*)(CPad*))0x5407F0;
    return original(pad);
}

class HoldToSprint {
public:
    HoldToSprint() {
        // Replace the call to CPad::SprintJustDown in ControlButtonSprint
        injector::MakeCALL(0x60A68D, SprintJustDownHook, true);
    }
} holdToSprint;