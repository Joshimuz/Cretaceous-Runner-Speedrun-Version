
// Test script for Industrial level

VAR_INT		player scplayer
VAR_INT		TEST_CAR test_char
VAR_FLOAT x_float_m y_float_m z_float_m player_heading_debug debug_car_heading
VAR_INT magic_car button_press_flag car_colour car_colour2
VAR_INT flag_create_car initial_create_car initial_car_selected counter_create_car

x_float_m = 0.0
y_float_m = 0.0
z_float_m = 0.0
player_heading_debug = 0.0
debug_car_heading = 0.0

magic_car = 0
button_press_flag = 0
car_colour = 0
car_colour2 = 0
flag_create_car = 0
initial_create_car = 0
initial_car_selected = 0
counter_create_car = 151 //CAR_CHEETAH


SCRIPT_NAME mainscr

//	SET_INTRO_IS_PLAYING FALSE

CREATE_PLAYER 0 1498.8 -1661.3 12.5 player
GET_PLAYER_CHAR player scplayer

DO_FADE 0 FADE_OUT

LOAD_SCENE 137.0 -1574.0 11.0

/*
REQUEST_MODEL CAR_CHEETAH

WHILE NOT HAS_MODEL_LOADED CAR_CHEETAH
 
	WAIT 0

ENDWHILE

CREATE_CAR CAR_CHEETAH -1138.406f -661.471f -100.0f TEST_CAR

MARK_MODEL_AS_NO_LONGER_NEEDED CAR_CHEETAH
*/

REQUEST_MODEL male01

WHILE NOT HAS_MODEL_LOADED male01
 
	WAIT 0

ENDWHILE

CREATE_CHAR PEDTYPE_CIVMALE male01 1500.0 -1660.0 13.0f test_char

//	MARK_MODEL_AS_NO_LONGER_NEEDED male01


DEBUG_ON

//LAUNCH_MISSION debug.sc

DO_FADE 1000 FADE_IN

MainLoop:

WAIT 0


	IF IS_PLAYER_PLAYING player
		IF IS_BUTTON_PRESSED PAD2 RIGHTSHOULDER1
		AND flag_create_car = 0
		AND button_press_flag = 0
			GET_CHAR_COORDINATES scplayer x_float_m y_float_m z_float_m
			GET_CHAR_HEADING scplayer player_heading_debug
			IF player_heading_debug < 45.0
			AND player_heading_debug > 0.0
				y_float_m += 5.0
				debug_car_heading = 90.0
			ENDIF
			IF player_heading_debug < 360.0
			AND player_heading_debug > 315.0
				y_float_m += 5.0
				debug_car_heading = 90.0
			ENDIF
			IF player_heading_debug < 135.0
			AND player_heading_debug > 45.0
				x_float_m -= 5.0
				debug_car_heading = 180.0
			ENDIF
			IF player_heading_debug < 225.0
			AND player_heading_debug > 135.0
				y_float_m -= 5.0
				debug_car_heading = 270.0
			ENDIF
			IF player_heading_debug < 315.0
			AND player_heading_debug > 225.0
				x_float_m += 5.0
				debug_car_heading = 0.0
			ENDIF
			z_float_m = z_float_m + 0.6
			GET_GROUND_Z_FOR_3D_COORD x_float_m y_float_m z_float_m	z_float_m
			REQUEST_MODEL counter_create_car
			WHILE NOT HAS_MODEL_LOADED counter_create_car
				
				WAIT 0
				
				PRINT_NOW LOADCAR 100 1 //"Loading vehicle, press pad2 leftshoulder1 to cancel"
				
				IF IS_BUTTON_PRESSED PAD2 LEFTSHOULDER1
					//++ counter_create_car
					GOTO next_carzzz
				ENDIF
			
			ENDWHILE
			
			CREATE_CAR counter_create_car x_float_m y_float_m z_float_m magic_car
			SET_CAR_HEADING	magic_car debug_car_heading
			
			LOCK_CAR_DOORS magic_car CARLOCK_UNLOCKED

			MARK_MODEL_AS_NO_LONGER_NEEDED counter_create_car
			MARK_CAR_AS_NO_LONGER_NEEDED magic_car

			next_carzzz:
			IF initial_create_car = 0
			
				IF counter_create_car = 151
				AND initial_car_selected = 0
					counter_create_car = 105 //BIKE_BIKE
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 105
				AND initial_car_selected = 0
					counter_create_car = 110 //CAR_TAXI
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 110	
				AND initial_car_selected = 0
					counter_create_car = 128 //CAR_CABBIE
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 128	
				AND initial_car_selected = 0
					counter_create_car = 116 //CAR_POLICE
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 116	
				AND initial_car_selected = 0
					counter_create_car = 97	//CAR_FIRETRUCK
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 97 
				AND initial_car_selected = 0
					counter_create_car = 106 //CAR_AMBULANCE
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 106	
				AND initial_car_selected = 0
					counter_create_car = 119 //CAR_BANSHEE
					initial_car_selected = 1
				ENDIF
			
				IF counter_create_car = 119	
				AND initial_car_selected = 0
					counter_create_car = 101 //CAR_INFERNUS
					initial_car_selected = 1
					initial_create_car = 1
				ENDIF
			
				IF counter_create_car = 101	
				AND initial_car_selected = 0
					counter_create_car = 92 //CAR_STINGER
					initial_car_selected = 1
					initial_create_car = 1
				ENDIF
			
			ELSE
				++ counter_create_car
			
				IF counter_create_car > 153
					counter_create_car = 90
				ENDIF
			
				IF counter_create_car =	140	//PLANE_AIRTRAIN
				OR counter_create_car = 141	//PLANE_DEADDODO
					counter_create_car = 142
				ENDIF
			
				IF counter_create_car =	124	//TRAIN_SUBWAY
				OR counter_create_car = 125	//HELI_POLICE
					counter_create_car = 126
				ENDIF
						
				IF counter_create_car = 131 //CAR_RCBANDIT 
					counter_create_car = 132
				ENDIF

				IF counter_create_car = 147 //HELI
					counter_create_car = 148
				ENDIF

			ENDIF
			flag_create_car = 1
			button_press_flag = 1
		ENDIF

		IF IS_BUTTON_PRESSED PAD2 LEFTSHOULDER1
		AND flag_create_car = 1
			IF NOT IS_CAR_DEAD magic_car
				GENERATE_RANDOM_INT_IN_RANGE 0 88 car_colour2
				CHANGE_CAR_COLOUR magic_car car_colour car_colour2 // 0 - 88
				++car_colour
				IF car_colour > 87
					car_colour = 0
				ENDIF
			ENDIF
		ENDIF

		IF NOT IS_BUTTON_PRESSED PAD2 RIGHTSHOULDER1
		AND button_press_flag = 1
			button_press_flag = 0
		ENDIF

		IF IS_BUTTON_PRESSED PAD2 RIGHTSHOULDER1
		AND flag_create_car = 1
		AND button_press_flag = 0
			IF IS_CAR_DEAD magic_car
				DELETE_CAR magic_car
			ELSE
				IF NOT IS_CHAR_IN_CAR scplayer magic_car
					DELETE_CAR magic_car
				ELSE
					MARK_CAR_AS_NO_LONGER_NEEDED magic_car
				ENDIF
			ENDIF 
			flag_create_car = 0
			initial_car_selected = 0
			button_press_flag = 1
		ENDIF
	ENDIF


GOTO MainLoop

TERMINATE_THIS_SCRIPT
