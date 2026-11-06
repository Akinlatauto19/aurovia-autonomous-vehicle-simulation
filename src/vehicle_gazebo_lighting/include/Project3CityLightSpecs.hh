#pragma once
#include <string>
#include <vector>

struct CityLightSpec
{
  std::string name;
  double x, y, z, range, intensity;
};

inline const std::vector<CityLightSpec> kProject3CityLightSpecs{
      // Zone 1: main urban road lighting (12 existing lamp heads)
      {"zone1_lamp_000_south", 8.0,  -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_000_north", 8.0,   5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_001_south", 22.0, -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_001_north", 22.0,  5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_002_south", 36.0, -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_002_north", 36.0,  5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_003_south", 50.0, -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_003_north", 50.0,  5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_004_south", 64.0, -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_004_north", 64.0,  5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_005_south", 77.0, -5.530, 5.050, 22.0, 5.0},
      {"zone1_lamp_005_north", 77.0,  5.530, 5.050, 22.0, 5.0},

    // Zone 2: garden curve lamps (6)
      {"zone2_garden_000_m1", 95.1839, -6.5550, 5.15, 22.0, 5.0},
      {"zone2_garden_000_p1", 90.7581, 9.9624, 5.15, 22.0, 5.0},
      {"zone2_garden_001_m1", 112.8359, 1.5665, 5.15, 22.0, 5.0},
      {"zone2_garden_001_p1", 102.8995, 15.4833, 5.15, 22.0, 5.0},
      {"zone2_garden_002_m1", 126.1403, 16.8901, 5.15, 22.0, 5.0},
      {"zone2_garden_002_p1", 110.8751, 24.5963, 5.15, 22.0, 5.0},

      // Zone 5: four corner streetlights (4)
      {"zone5_south_west", 101.8, 139.0, 5.05, 15.0, 3.0},
      {"zone5_south_east", 141.2, 139.0, 5.05, 15.0, 3.0},
      {"zone5_north_west", 101.8, 178.0, 5.05, 15.0, 3.0},
      {"zone5_north_east", 141.2, 178.0, 5.05, 15.0, 3.0},

      // Zone 6: cross-road streetlights (12)
      {"zone6_cross_south_55", 55.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_55", 55.0, 52.35, 5.05, 15.0, 3.0},
      {"zone6_cross_south_80", 80.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_80", 80.0, 52.35, 5.05, 15.0, 3.0},
      {"zone6_cross_south_105", 105.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_105", 105.0, 52.35, 5.05, 15.0, 3.0},
      {"zone6_cross_south_145", 145.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_145", 145.0, 52.35, 5.05, 15.0, 3.0},
      {"zone6_cross_south_170", 170.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_170", 170.0, 52.35, 5.05, 15.0, 3.0},
      {"zone6_cross_south_195", 195.0, 40.65, 5.05, 15.0, 3.0},
      {"zone6_cross_north_195", 195.0, 52.35, 5.05, 15.0, 3.0},

      // Zone 6: main road streetlights (6)
      {"zone6_main_left_60", 115.4210, 60.1038, 5.05, 15.0, 3.0},
      {"zone6_main_right_60", 126.5191, 59.8962, 5.05, 15.0, 3.0},
      {"zone6_main_left_74", 115.6829, 74.1038, 5.05, 15.0, 3.0},
      {"zone6_main_right_74", 126.7809, 73.8962, 5.05, 15.0, 3.0},
      {"zone6_main_left_88", 115.9447, 88.1038, 5.05, 15.0, 3.0},
      {"zone6_main_right_88", 127.0427, 87.8962, 5.05, 15.0, 3.0},

      // Zone 7: flyover deck lights (6)
      {"zone7_deck_south_1", 111.0, 42.8, 6.1, 12.0, 3.0},
      {"zone7_deck_south_2", 121.0, 42.8, 6.1, 12.0, 3.0},
      {"zone7_deck_south_3", 131.0, 42.8, 6.1, 12.0, 3.0},
      {"zone7_deck_north_1", 111.0, 50.28, 6.1, 12.0, 3.0},
      {"zone7_deck_north_2", 121.0, 50.28, 6.1, 12.0, 3.0},
      {"zone7_deck_north_3", 131.0, 50.28, 6.1, 12.0, 3.0},

      // Zone 7: under-flyover lights (3)
      {"zone7_underdeck_1", 110.0, 46.5395, 3.5, 9.0, 2.5},
      {"zone7_underdeck_2", 120.0, 46.5395, 3.5, 9.0, 2.5},
      {"zone7_underdeck_3", 130.0, 46.5395, 3.5, 9.0, 2.5},

      // Zone 8: west access ramp (7)
      {"zone8_west_1", 101.32, 130.05, 5.05, 14.0, 3.0},
      {"zone8_west_2", 79.72, 99.16, 5.05, 14.0, 3.0},
      {"zone8_west_3", 64.36, 77.36, 5.05, 14.0, 3.0},
      {"zone8_west_4", 93.24, 116.89, 5.05, 14.0, 3.0},
      {"zone8_west_5", 87.38, 109.03, 5.05, 14.0, 3.0},
      {"zone8_west_6", 72.09, 89.0, 5.05, 14.0, 3.0},
      {"zone8_west_7", 58.70, 66.42, 5.05, 14.0, 3.0},

      // Zone 8: east access ramp (7)
      {"zone8_east_1", 147.46, 119.3, 5.05, 14.0, 3.0},
      {"zone8_east_2", 162.32, 98.36, 5.05, 14.0, 3.0},
      {"zone8_east_3", 176.96, 76.0, 5.05, 14.0, 3.0},
      {"zone8_east_4", 140.36, 132.79, 5.05, 14.0, 3.0},
      {"zone8_east_5", 152.09, 112.47, 5.05, 14.0, 3.0},
      {"zone8_east_6", 169.64, 87.94, 5.05, 14.0, 3.0},
      {"zone8_east_7", 182.17, 64.82, 5.05, 14.0, 3.0},
  };
