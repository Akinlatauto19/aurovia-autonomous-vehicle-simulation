#include <atomic>
#include <iostream>
#include <string>
#include <vector>

#include <gz/gui/Application.hh>
#include <gz/gui/GuiEvents.hh>
#include <gz/gui/MainWindow.hh>
#include <gz/gui/Plugin.hh>

#include <gz/math/Color.hh>
#include <gz/plugin/Register.hh>
#include <gz/rendering/Light.hh>
#include <gz/rendering/RenderingIface.hh>
#include <gz/rendering/RenderEngine.hh>
#include <gz/rendering/Scene.hh>
#include <gz/rendering/Visual.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/transport/Node.hh>

#include <QObject>
#include <QEvent>

struct CityLightSpec
{
  std::string name;
  double x;
  double y;
  double z;
  double range;
  double intensity;
};

class Project3CityLightingPlugin : public gz::gui::Plugin
{
public:
  Project3CityLightingPlugin() = default;
  ~Project3CityLightingPlugin() override = default;

  void LoadConfig(const tinyxml2::XMLElement *) override
  {
    auto mainWindow =
        gz::gui::App()->findChild<gz::gui::MainWindow *>();

    if (mainWindow)
      mainWindow->installEventFilter(this);

    if (this->transportNode.Subscribe(
            "/city/day_night",
            &Project3CityLightingPlugin::cityLightingCallback,
            this))
    {
      std::cout
          << "[CityLighting] Listening on /city/day_night"
          << std::endl;
    }
    else
    {
      std::cerr
          << "[CityLighting] Subscription failed"
          << std::endl;
    }
  }

protected:
  bool eventFilter(QObject *_obj, QEvent *_event) override
  {
    if (_event->type() == gz::gui::events::Render::kType)
      this->updateLighting();

    return QObject::eventFilter(_obj, _event);
  }

private:
  // Each entry is positioned near the existing physical lamp head.
  // Zone 4 is deliberately excluded.
  const std::vector<CityLightSpec> lightSpecs{
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

  void cityLightingCallback(const gz::msgs::Boolean &_msg)
  {
    this->requestedOn.store(_msg.data());
  }

  void findScene()
  {
    const auto engines = gz::rendering::loadedEngines();
    if (engines.empty())
      return;

    auto engine = gz::rendering::engine(engines[0]);
    if (!engine || engine->SceneCount() == 0)
      return;

    auto candidate = engine->SceneByIndex(0);
    if (!candidate || !candidate->IsInitialized() ||
        !candidate->RootVisual())
      return;

    this->scene = candidate;
    this->sunLight = this->scene->LightByName("sun");

    if (this->sunLight)
      std::cout << "[CityLighting] Found rendering light 'sun'"
                << std::endl;
    else
      std::cerr << "[CityLighting] Rendering light 'sun' not found; "
                   "ambient and background switching will still work."
                << std::endl;
  }

  void createCityLights()
  {
    if (!this->scene || this->lightsCreated)
      return;

    auto root = this->scene->RootVisual();

    for (const auto &spec : this->lightSpecs)
    {
      auto light = this->scene->CreatePointLight(spec.name);

      if (!light)
      {
        std::cerr << "[CityLighting] Failed to create "
                  << spec.name << std::endl;
        continue;
      }

      light->SetDiffuseColor(gz::math::Color(1.0, 0.82, 0.62, 1.0));
      light->SetSpecularColor(gz::math::Color(1.0, 0.90, 0.75, 1.0));
      light->SetAttenuationRange(spec.range);
      light->SetAttenuationConstant(0.5);
      light->SetAttenuationLinear(0.04);
      light->SetAttenuationQuadratic(0.01);
      light->SetWorldPosition(spec.x, spec.y, spec.z);
      light->SetIntensity(0.0);
      root->AddChild(light);

      this->cityLights.push_back({light, spec.intensity, spec.name});
    }

    this->lightsCreated = true;

    std::cout << "[CityLighting] Created "
              << this->cityLights.size()
              << " rendering lights from "
              << this->lightSpecs.size()
              << " configured positions."
              << std::endl;
  }

  void applyLighting(const bool _night)
  {
    if (!this->scene)
      return;

    this->scene->SetSkyEnabled(!_night);

    // These values match the existing world scene's daylight appearance
    // approximately, while providing a darker background at night.
    if (_night)
    {
      this->scene->SetAmbientLight(
          gz::math::Color(0.035, 0.040, 0.060, 1.0));
      this->scene->SetBackgroundColor(
          gz::math::Color(0.008, 0.012, 0.030, 1.0));

      if (this->sunLight)
        this->sunLight->SetIntensity(0.0);
    }
    else
    {
      this->scene->SetAmbientLight(
          gz::math::Color(0.40, 0.40, 0.40, 1.0));
      this->scene->SetBackgroundColor(
          gz::math::Color(0.70, 0.70, 0.70, 1.0));

      if (this->sunLight)
        this->sunLight->SetIntensity(1.0);
    }

    for (auto &entry : this->cityLights)
      entry.light->SetIntensity(_night ? entry.nightIntensity : 0.0);

    this->appliedState = _night;

    std::cout << "[CityLighting] "
              << (_night ? "NIGHT" : "DAY")
              << " applied. Active city lights: "
              << (_night ? this->cityLights.size() : 0)
              << "/" << this->cityLights.size()
              << ". Sun rendering light: "
              << (this->sunLight ? "available" : "unavailable")
              << std::endl;
  }

  void updateLighting()
  {
    if (!this->scene)
      this->findScene();

    if (!this->scene)
      return;

    if (!this->lightsCreated)
      this->createCityLights();

    if (!this->lightsCreated)
      return;

    const bool desired = this->requestedOn.load();

    if (desired != this->appliedState || !this->initialStateApplied)
    {
      this->applyLighting(desired);
      this->initialStateApplied = true;
    }
  }

  struct ActiveCityLight
  {
    gz::rendering::PointLightPtr light;
    double nightIntensity;
    std::string name;
  };

  gz::rendering::ScenePtr scene;
  gz::rendering::LightPtr sunLight;
  std::vector<ActiveCityLight> cityLights;
  gz::transport::Node transportNode;
  std::atomic_bool requestedOn{false};
  bool lightsCreated{false};
  bool appliedState{false};
  bool initialStateApplied{false};
};

GZ_ADD_PLUGIN(Project3CityLightingPlugin, gz::gui::Plugin)
