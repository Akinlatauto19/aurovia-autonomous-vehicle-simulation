#include "vehicle_gazebo_lighting/Project3HeadlampPlugin.hh"

#include <iostream>

#include <gz/gui/Application.hh>
#include <gz/gui/GuiEvents.hh>
#include <gz/gui/MainWindow.hh>
#include <gz/math/Color.hh>
#include <gz/plugin/Register.hh>
#include <gz/rendering/Geometry.hh>
#include <gz/rendering/Mesh.hh>
#include <gz/rendering/RenderEngine.hh>
#include <gz/rendering/RenderingIface.hh>
#include <gz/rendering/Visual.hh>
#include <gz/msgs/boolean.pb.h>

void Project3HeadlampPlugin::LoadConfig(
    const tinyxml2::XMLElement *)
{
  auto mainWindow =
      gz::gui::App()->findChild<gz::gui::MainWindow *>();

  if (mainWindow)
    mainWindow->installEventFilter(this);

  const bool subscribed = this->transportNode.Subscribe(
      "/vehicle/headlamp_state",
      &Project3HeadlampPlugin::headlampCallback,
      this);

  if (!subscribed)
  {
    std::cerr
        << "[Project3HeadlampPlugin] Failed to subscribe to "
        << "/vehicle/headlamp_state"
        << std::endl;
  }
  else
  {
    std::cout
        << "[Project3HeadlampPlugin] Listening on "
        << "/vehicle/headlamp_state"
        << std::endl;
  }
}

void Project3HeadlampPlugin::headlampCallback(
    const gz::msgs::Boolean &_msg)
{
  this->requestedOn.store(_msg.data());

  std::cout
      << "[Project3HeadlampPlugin] HEADLAMP COMMAND RECEIVED: "
      << (_msg.data() ? "ON" : "OFF")
      << std::endl;
}

bool Project3HeadlampPlugin::eventFilter(
    QObject *_obj,
    QEvent *_event)
{
  if (_event->type() == gz::gui::events::Render::kType)
  {
    this->updateHeadlamp();
  }

  return QObject::eventFilter(_obj, _event);
}

void Project3HeadlampPlugin::findScene()
{
  auto engines = gz::rendering::loadedEngines();

  if (engines.empty())
    return;

  auto engine = gz::rendering::engine(engines[0]);

  if (!engine || engine->SceneCount() == 0)
    return;

  auto scenePtr = engine->SceneByIndex(0);

  if (!scenePtr ||
      !scenePtr->IsInitialized() ||
      !scenePtr->RootVisual())
  {
    return;
  }

  this->scene = scenePtr;
}

void Project3HeadlampPlugin::updateHeadlamp()
{
  static unsigned int renderCount = 0;
  ++renderCount;

  if (renderCount <= 20)
  {
    std::cout
        << "[Project3HeadlampPlugin] updateHeadlamp call #"
        << renderCount
        << std::endl;
  }

  if (!this->scene)
  {
    this->findScene();

    if (!this->scene)
      return;
  }

  if (!this->materialFound)
  {
    auto visual = this->scene->VisualByName(
        "audibot::chassis::visual_chassis");

    if (!visual)
    {
      std::cout
          << "[Project3HeadlampPlugin] visual_chassis NOT found."
          << std::endl;

      std::cout
          << "[Project3HeadlampPlugin] Scene visual count: "
          << this->scene->VisualCount()
          << std::endl;

      for (unsigned int k = 0;
           k < this->scene->VisualCount();
           ++k)
      {
        auto sceneVisual = this->scene->VisualByIndex(k);

        if (sceneVisual)
        {
          std::cout
              << "[Project3HeadlampPlugin] Scene visual: "
              << sceneVisual->Name()
              << std::endl;
        }
      }

      return;
    }

    std::cout
        << "[Project3HeadlampPlugin] chassis found. Geometry count: "
        << visual->GeometryCount()
        << std::endl;

    std::cout
        << "[Project3HeadlampPlugin] Child visual count: "
        << visual->ChildCount()
        << std::endl;

    for (unsigned int i = 0;
         i < visual->ChildCount();
         ++i)
    {
      auto child = visual->ChildByIndex(i);

      if (child)
      {
        std::cout
            << "[Project3HeadlampPlugin] Child visual #"
            << i
            << ": "
            << child->Name()
            << std::endl;
      }
    }

    for (unsigned int i = 0;
         i < visual->GeometryCount();
         ++i)
    {
      auto geometry = visual->GeometryByIndex(i);

      if (geometry)
      {
        std::cout
            << "[Project3HeadlampPlugin] Geometry #"
            << i
            << " found."
            << std::endl;
      }

      auto mesh =
          std::dynamic_pointer_cast<gz::rendering::Mesh>(
              geometry);

      if (!mesh)
        continue;

      for (unsigned int j = 0;
           j < mesh->SubMeshCount();
           ++j)
      {
        auto subMesh = mesh->SubMeshByIndex(j);

        if (!subMesh)
          continue;

        auto material = subMesh->Material();

        if (!material)
          continue;

        const std::string materialName = material->Name();
        const std::string subMeshName = subMesh->Name();

        if (j == 32)
        {
          std::cout
              << "[Project3HeadlampPlugin] TARGET SubMesh #32"
              << " | Name: " << subMeshName
              << " | Material: " << materialName
              << std::endl;
        }

       std::cout
       << "[Project3HeadlampPlugin] "
       << "Submesh: " << subMeshName
       << " | Material: " << materialName
       << std::endl;


        if (j == 32)
        {
          this->headlampMaterial =
              material->Clone("project3_headlamp_material");

          if (this->headlampMaterial)
          {
            subMesh->SetMaterial(
                this->headlampMaterial,
                false);

            this->materialFound = true;

            std::cout
                << "[Project3HeadlampPlugin] Found headlamp material: "
                << materialName
                << " / submesh: "
                << subMeshName
                << std::endl;
          }

          break;
        }
      }

      if (this->materialFound)
        break;
    }

    if (!this->materialFound)
      return;
  }

  const bool desiredState =
      this->requestedOn.load();

  if (desiredState == this->appliedState)
    return;

  if (desiredState)
  {
    // White emissive light when the headlamps are ON.
    this->headlampMaterial->SetEmissive(
        1.0, 1.0, 1.0, 1.0);

    std::cout
        << "[Project3HeadlampPlugin] HEADLAMPS ON"
        << std::endl;
  }
  else
  {
    // Existing Audibot headlamp material is non-emissive.
    this->headlampMaterial->SetEmissive(
        0.0, 0.0, 0.0, 1.0);

    std::cout
        << "[Project3HeadlampPlugin] HEADLAMPS OFF"
        << std::endl;
  }

  this->appliedState = desiredState;
}

GZ_ADD_PLUGIN(
    Project3HeadlampPlugin,
    gz::gui::Plugin)
