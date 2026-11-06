#include <atomic>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

#include <gz/common/Event.hh>
#include <gz/math/Color.hh>
#include <gz/plugin/Register.hh>
#include <gz/rendering/Light.hh>
#include <gz/rendering/RenderEngine.hh>
#include <gz/rendering/RenderingIface.hh>
#include <gz/rendering/Scene.hh>
#include <gz/rendering/Visual.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/transport/Node.hh>
#include <gz/sim/System.hh>
#include <gz/sim/EventManager.hh>
#include <gz/sim/rendering/Events.hh>

#include "Project3CityLightSpecs.hh"

class Project3CameraLightingSystem :
    public gz::sim::System,
    public gz::sim::ISystemConfigure
{
  public: void Configure(
      const gz::sim::Entity &,
      const std::shared_ptr<const sdf::Element> &,
      gz::sim::EntityComponentManager &,
      gz::sim::EventManager &_eventMgr) override
  {
    this->node.Subscribe(
        "/city/day_night",
        &Project3CameraLightingSystem::OnDayNight, this);

    this->connection =
        _eventMgr.Connect<gz::sim::events::PreRender>(
          std::bind(
            &Project3CameraLightingSystem::OnPreRender, this));

    std::cout << "[CameraLighting] Server camera lighting system loaded."
              << std::endl;
  }

  private: void OnDayNight(const gz::msgs::Boolean &_msg)
  {
    this->nightRequested.store(_msg.data());
  }

  private: void FindScene()
  {
    const auto engines = gz::rendering::loadedEngines();
    if (engines.empty())
      return;

    auto engine = gz::rendering::engine(engines.front());
    if (!engine || engine->SceneCount() == 0)
      return;

    auto candidate = engine->SceneByIndex(0);
    if (!candidate || !candidate->IsInitialized() ||
        !candidate->RootVisual())
      return;

    this->scene = candidate;
    this->sun = this->scene->LightByName("sun");

    std::cout << "[CameraLighting] Server rendering scene found."
              << std::endl;
  }

  private: void CreateLights()
  {
    if (!this->scene || this->lightsCreated)
      return;

    auto root = this->scene->RootVisual();

    for (const auto &spec : kProject3CityLightSpecs)
    {
      auto light = this->scene->CreatePointLight(spec.name);
      if (!light)
      {
        std::cerr << "[CameraLighting] Could not create "
                  << spec.name << std::endl;
        continue;
      }

      light->SetDiffuseColor(
          gz::math::Color(1.0, 0.82, 0.62, 1.0));
      light->SetSpecularColor(
          gz::math::Color(1.0, 0.90, 0.75, 1.0));
      light->SetAttenuationRange(spec.range);
      light->SetAttenuationConstant(0.5);
      light->SetAttenuationLinear(0.04);
      light->SetAttenuationQuadratic(0.01);
      light->SetWorldPosition(spec.x, spec.y, spec.z);
      light->SetIntensity(0.0);
      root->AddChild(light);

      this->lights.push_back({light, spec.intensity});
    }

    this->lightsCreated = true;
    std::cout << "[CameraLighting] Created "
              << this->lights.size()
              << " camera-scene streetlights." << std::endl;
  }

  private: void ApplyLighting(bool night)
  {
    if (!this->scene)
      return;

    this->scene->SetSkyEnabled(!night);

    if (night)
    {
      this->scene->SetAmbientLight(
          gz::math::Color(0.035, 0.040, 0.060, 1.0));
      this->scene->SetBackgroundColor(
          gz::math::Color(0.008, 0.012, 0.030, 1.0));
      if (this->sun)
        this->sun->SetIntensity(0.0);
    }
    else
    {
      this->scene->SetAmbientLight(
          gz::math::Color(0.40, 0.40, 0.40, 1.0));
      this->scene->SetBackgroundColor(
          gz::math::Color(0.70, 0.70, 0.70, 1.0));
      if (this->sun)
        this->sun->SetIntensity(1.0);
    }

    for (auto &entry : this->lights)
      entry.light->SetIntensity(night ? entry.intensity : 0.0);

    this->appliedState = night;
    this->stateApplied = true;

    std::cout << "[CameraLighting] "
              << (night ? "NIGHT" : "DAY")
              << " applied to camera rendering scene; active lamps: "
              << (night ? this->lights.size() : 0)
              << "/" << this->lights.size() << std::endl;
  }

  private: void OnPreRender()
  {
    if (!this->scene)
      this->FindScene();
    if (!this->scene)
      return;

    if (!this->lightsCreated)
      this->CreateLights();

    const bool requested = this->nightRequested.load();
    if (!this->stateApplied || requested != this->appliedState)
      this->ApplyLighting(requested);
  }

  private: struct CameraLight
  {
    gz::rendering::PointLightPtr light;
    double intensity;
  };

  private: gz::rendering::ScenePtr scene;
  private: gz::rendering::LightPtr sun;
  private: gz::transport::Node node;
  private: gz::common::ConnectionPtr connection;
  private: std::atomic_bool nightRequested{false};
  private: std::vector<CameraLight> lights;
  private: bool lightsCreated{false};
  private: bool stateApplied{false};
  private: bool appliedState{false};
};

GZ_ADD_PLUGIN(
    Project3CameraLightingSystem,
    gz::sim::System,
    Project3CameraLightingSystem::ISystemConfigure)
GZ_ADD_PLUGIN_ALIAS(
    Project3CameraLightingSystem,
    "project3::CameraLighting")
