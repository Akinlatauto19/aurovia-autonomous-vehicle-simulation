#include <algorithm>
#include <array>
#include <chrono>
#include <iostream>
#include <string>
#include <vector>

#include <QObject>
#include <QEvent>
#include <QQuickWindow>

#include <gz/gui/GuiEvents.hh>
#include <gz/gui/MainWindow.hh>
#include <gz/gui/Plugin.hh>
#include <gz/gui/Application.hh>

#include <gz/math/Color.hh>
#include <gz/plugin/Register.hh>
#include <gz/rendering/RenderingIface.hh>
#include <gz/rendering/RenderEngine.hh>
#include <gz/rendering/Scene.hh>
#include <gz/rendering/Visual.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/rendering/Material.hh>
#include <QTimer>

namespace
{
enum class SignalColour
{
  Red,
  Amber,
  Green
};

enum class Phase
{
  StartupAllRed,
  SouthGreen,
  SouthAmber,
  SouthAllRed,
  NorthGreen,
  NorthAmber,
  NorthAllRed
};

struct Lens
{
  std::string name;
  std::string visualName;
  SignalColour colour;
  gz::rendering::VisualPtr visual;
  gz::rendering::MaterialPtr material;
};

constexpr auto ALL_RED_SECONDS = std::chrono::seconds(1);
constexpr auto GREEN_SECONDS = std::chrono::seconds(15);
constexpr auto AMBER_SECONDS = std::chrono::seconds(3);

const char *colourName(SignalColour colour)
{
  switch (colour)
  {
    case SignalColour::Red: return "RED";
    case SignalColour::Amber: return "AMBER";
    case SignalColour::Green: return "GREEN";
  }
  return "UNKNOWN";
}
}

class Project3TrafficLightsPlugin : public gz::gui::Plugin
{
public:
  Project3TrafficLightsPlugin()
  {
    this->lenses = {
      {"zone3_signal_south_red_lens",
       "zone3_traffic_light_south::zone3_traffic_light_south_link::zone3_signal_south_red_lens",
       SignalColour::Red, nullptr, nullptr},
      {"zone3_signal_south_amber_lens",
       "zone3_traffic_light_south::zone3_traffic_light_south_link::zone3_signal_south_amber_lens",
       SignalColour::Amber, nullptr, nullptr},
      {"zone3_signal_south_green_lens",
       "zone3_traffic_light_south::zone3_traffic_light_south_link::zone3_signal_south_green_lens",
       SignalColour::Green, nullptr, nullptr},
      {"zone3_signal_north_red_lens",
       "zone3_traffic_light_north::zone3_traffic_light_north_link::zone3_signal_north_red_lens",
       SignalColour::Red, nullptr, nullptr},
      {"zone3_signal_north_amber_lens",
       "zone3_traffic_light_north::zone3_traffic_light_north_link::zone3_signal_north_amber_lens",
       SignalColour::Amber, nullptr, nullptr},
      {"zone3_signal_north_green_lens",
       "zone3_traffic_light_north::zone3_traffic_light_north_link::zone3_signal_north_green_lens",
       SignalColour::Green, nullptr, nullptr}
    };
  }

  ~Project3TrafficLightsPlugin() override = default;

  void LoadConfig(const tinyxml2::XMLElement *) override
  {
    this->southStatePub =
        this->transportNode.Advertise<gz::msgs::StringMsg>(
            "/project3/traffic_light/south_state");
    this->northStatePub =
        this->transportNode.Advertise<gz::msgs::StringMsg>(
            "/project3/traffic_light/north_state");

    auto *timer = new QTimer(this);
    timer->setInterval(50);

    QObject::connect(
        timer, &QTimer::timeout, this,
        [this]()
        {
          ++this->timerTicks;
          if (this->timerTicks == 1 || this->timerTicks % 100 == 0)
          {
            std::cout << "[TrafficLights][DIAGNOSTIC] Timer callback count: "
                      << this->timerTicks << std::endl;
          }
          this->updateController();
          this->publishSignalStates();
        });

    timer->start();

    std::cout
        << "[TrafficLights] Timer-based controller started. "
        << "Interval: 50 ms. Startup phase: ALL RED."
        << std::endl;
  }

protected:
  bool eventFilter(QObject *_obj, QEvent *_event) override
  {
    if (_event->type() == gz::gui::events::Render::kType)
      this->updateController();

    return QObject::eventFilter(_obj, _event);
  }

private:
  void findScene()
  {
    ++this->sceneSearches;
    if (this->sceneSearches == 1 || this->sceneSearches % 100 == 0)
    {
      const auto engines = gz::rendering::loadedEngines();
      std::cout << "[TrafficLights][DIAGNOSTIC] Scene search "
                << this->sceneSearches << ", loaded engines: "
                << engines.size() << std::endl;
      for (const auto &engineName : engines)
      {
        auto engine = gz::rendering::engine(engineName);
        if (engine)
          std::cout << "[TrafficLights][DIAGNOSTIC] Engine "
                    << engineName << ", scenes: "
                    << engine->SceneCount() << std::endl;
      }
    }

    const auto engineNames = gz::rendering::loadedEngines();

    for (const auto &engineName : engineNames)
    {
      auto engine = gz::rendering::engine(engineName);

      if (!engine)
        continue;

      for (unsigned int sceneIndex = 0;
           sceneIndex < engine->SceneCount();
           ++sceneIndex)
      {
        auto candidate = engine->SceneByIndex(sceneIndex);

        if (!candidate || !candidate->IsInitialized() ||
            !candidate->RootVisual())
          continue;

        // Diagnostic: inspect the rendering scene and test every expected lens.
        if (this->sceneSearches == 1 || this->sceneSearches % 100 == 0)
        {
          std::cout << "[TrafficLights][DIAGNOSTIC] Candidate scene: "
                    << candidate->Name()
                    << ", visuals: " << candidate->VisualCount()
                    << std::endl;

          const unsigned int count = candidate->VisualCount();
          const unsigned int limit = count;

          for (unsigned int i = 0; i < limit; ++i)
          {
            auto visual = candidate->VisualByIndex(i);
            if (visual)
            {
              const auto name = visual->Name();
              if (name.find("zone3") != std::string::npos ||
                  name.find("traffic") != std::string::npos ||
                  name.find("signal") != std::string::npos ||
                  name.find("lens") != std::string::npos)
              {
                std::cout << "[TrafficLights][DIAGNOSTIC] Visual[" << i
                          << "]: " << name << std::endl;
              }
            }
          }

          for (const auto &lens : this->lenses)
          {
            std::cout << "[TrafficLights][DIAGNOSTIC] Expected lens "
                      << lens.name << ": "
                      << (candidate->VisualByName(lens.visualName)
                              ? "FOUND" : "NOT FOUND")
                      << std::endl;
          }
        }

        // Keep the existing selection rule: only accept a scene containing
        // every expected signal lens.
        bool allLensesFound = true;

        for (const auto &lens : this->lenses)
        {
          if (!candidate->VisualByName(lens.visualName))
          {
            allLensesFound = false;
            break;
          }
        }

        if (!allLensesFound)
          continue;

        this->scene = candidate;

        std::cout << "[TrafficLights] Correct rendering scene found: "
                  << engineName << ", scene " << sceneIndex
                  << ", visual count " << candidate->VisualCount()
                  << ". All six signal lenses are present."
                  << std::endl;

        return;
      }
    }
  }

  bool initializeLenses()
  {
    if (!this->scene)
      return false;

    for (auto &lens : this->lenses)
    {
      lens.visual = this->scene->VisualByName(lens.visualName);

      if (!lens.visual)
      {
        std::cerr << "[TrafficLights] Waiting for visual: "
                  << lens.name << std::endl;
        for (auto &entry : this->lenses)
          entry.visual.reset();
        return false;
      }
    }

    for (auto &lens : this->lenses)
    {
      lens.material = this->scene->CreateMaterial(
          "project3_dynamic_" + lens.name);

      if (!lens.material)
      {
        std::cerr << "[TrafficLights] Could not create material for "
                  << lens.name << std::endl;
        return false;
      }

      // Each lens gets its own material, so changing a signal cannot
      // unintentionally change another city object.
      lens.visual->SetMaterial(lens.material, false);
    }

    this->lensesReady = true;

    std::cout << "[TrafficLights] All six signal lenses found."
              << std::endl;

    this->applyPhase();
    return true;
  }

  void setLens(Lens &lens, bool active)
  {
    double r = 0.0;
    double g = 0.0;
    double b = 0.0;

    switch (lens.colour)
    {
      case SignalColour::Red:
        r = 1.0;
        break;

      case SignalColour::Amber:
        r = 1.0;
        g = 0.42;
        break;

      case SignalColour::Green:
        g = 1.0;
        break;
    }

    // These are dedicated materials created by this controller.
    // Disable scene lighting so each lens is controlled by its own
    // explicitly assigned colour rather than ambient scene lighting.
    lens.material->SetLightingEnabled(false);

    if (active)
    {
      lens.material->SetAmbient(r, g, b, 1.0);
      lens.material->SetDiffuse(r, g, b, 1.0);
      lens.material->SetEmissive(r, g, b, 1.0);
    }
    else
    {
      // Unlit lenses should look like dark coloured glass.
      lens.material->SetAmbient(r * 0.015, g * 0.015, b * 0.015, 1.0);
      lens.material->SetDiffuse(r * 0.025, g * 0.025, b * 0.025, 1.0);
      lens.material->SetEmissive(0.0, 0.0, 0.0, 1.0);
    }
  }

  void applyPhase()
  {
    bool southRed = true;
    bool southAmber = false;
    bool southGreen = false;

    bool northRed = true;
    bool northAmber = false;
    bool northGreen = false;

    switch (this->phase)
    {
      case Phase::StartupAllRed:
      case Phase::SouthAllRed:
      case Phase::NorthAllRed:
        break;

      case Phase::SouthGreen:
        southRed = false;
        southGreen = true;
        break;

      case Phase::SouthAmber:
        southRed = false;
        southAmber = true;
        break;

      case Phase::NorthGreen:
        northRed = false;
        northGreen = true;
        break;

      case Phase::NorthAmber:
        northRed = false;
        northAmber = true;
        break;
    }

    const std::array<bool, 6> active{
      southRed, southAmber, southGreen,
      northRed, northAmber, northGreen
    };

    for (std::size_t i = 0; i < this->lenses.size(); ++i)
      this->setLens(this->lenses[i], active[i]);

    std::cout << "[TrafficLights] Phase: "
              << this->phaseName()
              << " | South: "
              << colourName(southRed ? SignalColour::Red :
                  southAmber ? SignalColour::Amber : SignalColour::Green)
              << " | North: "
              << colourName(northRed ? SignalColour::Red :
                  northAmber ? SignalColour::Amber : SignalColour::Green)
              << std::endl;

    this->phaseStart = std::chrono::steady_clock::now();
  }

  const char *phaseName() const
  {
    switch (this->phase)
    {
      case Phase::StartupAllRed: return "STARTUP ALL-RED";
      case Phase::SouthGreen: return "SOUTH GREEN";
      case Phase::SouthAmber: return "SOUTH AMBER";
      case Phase::SouthAllRed: return "SOUTH CLEARANCE ALL-RED";
      case Phase::NorthGreen: return "NORTH GREEN";
      case Phase::NorthAmber: return "NORTH AMBER";
      case Phase::NorthAllRed: return "NORTH CLEARANCE ALL-RED";
    }
    return "UNKNOWN";
  }

  std::chrono::steady_clock::duration phaseDuration() const
  {
    switch (this->phase)
    {
      case Phase::StartupAllRed:
      case Phase::SouthAllRed:
      case Phase::NorthAllRed:
        return ALL_RED_SECONDS;

      case Phase::SouthGreen:
      case Phase::NorthGreen:
        return GREEN_SECONDS;

      case Phase::SouthAmber:
      case Phase::NorthAmber:
        return AMBER_SECONDS;
    }

    return ALL_RED_SECONDS;
  }

  void advancePhase()
  {
    switch (this->phase)
    {
      case Phase::StartupAllRed:
      case Phase::NorthAllRed:
        this->phase = Phase::SouthGreen;
        break;

      case Phase::SouthGreen:
        this->phase = Phase::SouthAmber;
        break;

      case Phase::SouthAmber:
        this->phase = Phase::SouthAllRed;
        break;

      case Phase::SouthAllRed:
        this->phase = Phase::NorthGreen;
        break;

      case Phase::NorthGreen:
        this->phase = Phase::NorthAmber;
        break;

      case Phase::NorthAmber:
        this->phase = Phase::NorthAllRed;
        break;
    }

    this->applyPhase();
  }

  void updateController()
  {
    if (!this->scene)
      this->findScene();

    if (!this->scene)
      return;

    if (!this->lensesReady && !this->initializeLenses())
      return;

    const auto elapsed =
        std::chrono::steady_clock::now() - this->phaseStart;

    if (elapsed >= this->phaseDuration())
      this->advancePhase();
  }

  void publishSignalStates()
  {
    const char *south = "RED";
    const char *north = "RED";

    switch (this->phase)
    {
      case Phase::SouthGreen: south = "GREEN"; break;
      case Phase::SouthAmber: south = "AMBER"; break;
      case Phase::NorthGreen: north = "GREEN"; break;
      case Phase::NorthAmber: north = "AMBER"; break;
      default: break;
    }

    gz::msgs::StringMsg southMsg;
    southMsg.set_data(south);
    this->southStatePub.Publish(southMsg);

    gz::msgs::StringMsg northMsg;
    northMsg.set_data(north);
    this->northStatePub.Publish(northMsg);
  }

  gz::transport::Node transportNode;
  gz::transport::Node::Publisher southStatePub;
  gz::transport::Node::Publisher northStatePub;

  gz::rendering::ScenePtr scene;
  std::vector<Lens> lenses;
  std::size_t timerTicks{0};
  std::size_t sceneSearches{0};
  bool lensesReady{false};
  Phase phase{Phase::StartupAllRed};
  std::chrono::steady_clock::time_point phaseStart{
      std::chrono::steady_clock::now()};
};

GZ_ADD_PLUGIN(Project3TrafficLightsPlugin, gz::gui::Plugin)
