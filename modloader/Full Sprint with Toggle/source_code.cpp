#include <plugin.h>
#include <CMessages.h>
#include <CHud.h>
#include <CVehicle.h>

using namespace plugin;

// Toggle flags
static bool gHoldToSprint = true;
static bool gFullCycle = false;

// INI file path
static const std::string INI_FILE = "HoldToSprint.ini";

// Function to load settings from INI file
void LoadINISettings() {
    std::ifstream file(INI_FILE);
    if (file.is_open()) {
        std::string line;
        while (std::getline(file, line)) {
            // Remove whitespace and comments
            line.erase(0, line.find_first_not_of(" \t"));
            if (line.empty() || line[0] == ';' || line[0] == '#') continue;

            // Look for FullCycle setting
            if (line.find("FullCycle=") == 0) {
                std::string value = line.substr(9); // Skip "FullCycle="
                gFullCycle = (value == "1" || value == "true");
            }
        }
        file.close();
    }
    else {
        // Create INI file with default settings if it doesn't exist
        std::ofstream outfile(INI_FILE);
        if (outfile.is_open()) {
            outfile << "[Settings]\n";
            outfile << "FullCycle=0\n";
            outfile.close();
        }
    }
}

// Function to save settings to INI file
void SaveINISettings() {
    std::ofstream file(INI_FILE);
    if (file.is_open()) {
        file << "[Settings]\n";
        file << "FullCycle=" << (gFullCycle ? "1" : "0") << "\n";
        file.close();
    }
}

// Function to check if player is in a bike
bool IsPlayerInBike() {
    CVehicle* playerVehicle = FindPlayerVehicle(-1, false);
    if (playerVehicle) {
        // Check if vehicle is a bike
        switch (playerVehicle->m_nVehicleClass) {
        case VEHICLE_BIKE:
            return true;
        case VEHICLE_BMX:
            return true;
        default:
            return false;
        }
    }
    return false;
}

// Hook for CPad::SprintJustDown
bool __fastcall SprintJustDownHook(CPad* pad) {
    static unsigned int lastKeyPressedSprint = 0;
    static unsigned int lastKeyPressedCycle = 0;

    // Toggle gHoldToSprint with F8
    if (KeyPressed(VK_F8) && CTimer::m_snTimeInMilliseconds - lastKeyPressedSprint > 500) {
        lastKeyPressedSprint = CTimer::m_snTimeInMilliseconds;
        gHoldToSprint = !gHoldToSprint;
        CHud::SetHelpMessage(gHoldToSprint ? "FullSprint: ~g~Enabled~w~" : "FullSprint: ~r~Disabled~w~", true, false, false);
        SaveINISettings(); // Save settings when toggled
    }

    // Toggle gFullCycle with F9
    if (KeyPressed(VK_F9) && CTimer::m_snTimeInMilliseconds - lastKeyPressedCycle > 500) {
        lastKeyPressedCycle = CTimer::m_snTimeInMilliseconds;
        gFullCycle = !gFullCycle;
        CHud::SetHelpMessage(gFullCycle ? "FullCycle: ~g~Enabled~w~" : "FullCycle: ~r~Disabled~w~", true, false, false);
        SaveINISettings(); // Save settings when toggled
    }

    // If feature disabled, call original function
    if (!gHoldToSprint) {
        static auto original = (bool(__thiscall*)(CPad*))0x5407F0;
        return original(pad);
    }


    // If player is in a bike and FullCycle is active, make them super cycle.
    if (IsPlayerInBike() && gFullCycle && pad->GetSprint())
    {
        return true;
    }
    // If the run key is held and player is not in a vehicle, make them super sprint.
    else if (pad->GetSprint() && !FindPlayerPed()->bInVehicle)
    {
        return true;
    }

    // Otherwise, fall back to normal sprint logic
    static auto original = (bool(__thiscall*)(CPad*))0x5407F0;
    return original(pad);
}

class HoldToSprint {
public:
    HoldToSprint() {
        // Load settings from INI file
        LoadINISettings();

        // Replace the call to CPad::SprintJustDown in ControlButtonSprint
        injector::MakeCALL(0x60A68D, SprintJustDownHook, true);
    }
} holdToSprint;