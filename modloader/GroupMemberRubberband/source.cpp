#include <plugin.h>
#include <game_sa/CPools.h>
#include <game_sa/CPed.h>
#include <game_sa/CHud.h>
#include <game_sa/CFont.h>
#include <game_sa/CTimer.h>
#include <game_sa/CWorld.h>
#include <game_sa/CPedGroup.h>
#include <game_sa/CPedGroups.h>
#include <game_sa/CPedGroupMembership.h>
#include <game_sa/CPlayerPed.h>
#include <game_sa/CAnimBlendAssociation.h>
#include <game_sa/CAnimManager.h>
#include <game_sa/CMessages.h>

using namespace plugin;

enum class ERubberbandMode {
    Off,
    Speed,
    Teleport
};

class GroupMemberRubberband {
public:
    static inline ERubberbandMode gMode = ERubberbandMode::Off;
    static inline bool gKeyPressed = false;

    GroupMemberRubberband() {
        Events::gameProcessEvent += [] {

            // --- Handle Mode Toggle ---
            if (KeyPressed(VK_F10)) {
                if (!gKeyPressed) {
                    gKeyPressed = true;
                    CycleMode();
                }
            }
            else {
                gKeyPressed = false;
            }

            CPed* player = FindPlayerPed();
            if (!player)
                return;

            // If off, skip processing
            if (gMode == ERubberbandMode::Off)
                return;

            // Get player's group
            CPedGroup* group = reinterpret_cast<CPedGroup*>(CPedGroups::GetPedsGroup(player));
            if (!group)
                return;

            CPedGroupMembership* membership = &group->m_groupMembership;
            if (!membership)
                return;

            CVector playerPos = player->GetPosition();
            float playerHeading = player->m_fCurrentRotation;

            for (int i = 0; i < membership->CountMembers(); i++) {
                CPed* ped = membership->GetMember(i);
                if (!ped || ped == player)
                    continue;

                float dist = DistanceBetweenPoints(ped->GetPosition(), playerPos);

                if (gMode == ERubberbandMode::Speed) {
                    // SPEED UP MODE: Adjust animation speed
                    CAnimBlendAssociation* assoc = RpAnimBlendClumpGetFirstAssociation(ped->m_pRwClump);
                    if (!assoc)
                        continue;

                    for (CAnimBlendAssociation* a = assoc; a; a = RpAnimBlendGetNextAssociation(a)) {
                        
                        if (ped->bIsInTheAir)
                        {
                            ped->m_fHealth = 1000.0f;
                        }
                        
                        if (dist > 50.0f) {
                            if (a->m_fSpeed < 2.9f) {
                                a->m_fSpeed = 3.0f;
                            }
                        }
                        else if (dist < 20.0f) {
                            if (a->m_fSpeed > 1.1f)
                            {
                                a->m_fSpeed = 1.0f;
                            }
                        }
                    }
                }
                else if (gMode == ERubberbandMode::Teleport) {
                    // TELEPORT MODE: Move ped behind player if far
                    if (dist > 50.0f) {
                        // playerHeading is between -π and π radians. So negating it gives the opposite direction.
                        float randomBehindAngle = ((float)rand() / RAND_MAX) * (3.14159f * 1.0f / 3.0f) - playerHeading;

                        float radius = 10.0f + ((float)rand() / RAND_MAX) * 5.0f; // 10–15 units away
                        float offsetX = cosf(randomBehindAngle) * radius;
                        float offsetY = sinf(randomBehindAngle) * radius;

                        CVector newPos = playerPos;
                        newPos.x += offsetX;
                        newPos.y += offsetY;

                        newPos.z = CWorld::FindGroundZForCoord(newPos.x, newPos.y);

                        newPos.z += 0.5f; // Slightly above the ground Z to avoid getting stuck

                        ped->Teleport(newPos, false);
                        ped->SetHeading(playerHeading);
                    }
                }
            }
        };
    }

    static void CycleMode() {
        switch (gMode) {
        case ERubberbandMode::Off:
            gMode = ERubberbandMode::Speed;
            CHud::SetHelpMessage("Rubberband Mode: ~G~Speed x3", false, false, false);
            break;
        case ERubberbandMode::Speed:
            gMode = ERubberbandMode::Teleport;
            CHud::SetHelpMessage("Rubberband Mode: ~B~Teleport", false, false, false);
            break;
        case ERubberbandMode::Teleport:
            gMode = ERubberbandMode::Off;
            CHud::SetHelpMessage("Rubberband Mode: ~R~Off", false, false, false);
            break;
        }
    }
} GroupMemberRubberband;
