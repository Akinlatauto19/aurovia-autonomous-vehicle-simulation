#ifndef VEHICLE_GAZEBO_LIGHTING_PROJECT3_HEADLAMP_PLUGIN_HH_
#define VEHICLE_GAZEBO_LIGHTING_PROJECT3_HEADLAMP_PLUGIN_HH_

#include <atomic>

#include <gz/gui/Plugin.hh>
#include <gz/rendering/Material.hh>
#include <gz/rendering/Scene.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/boolean.pb.h>

#include <QObject>

class Project3HeadlampPlugin : public gz::gui::Plugin
{
public:
  Project3HeadlampPlugin() = default;
  ~Project3HeadlampPlugin() override = default;

  void LoadConfig(const tinyxml2::XMLElement *_pluginElem) override;

protected:
  bool eventFilter(QObject *_obj, QEvent *_event) override;

private:
  void headlampCallback(const gz::msgs::Boolean &_msg);

  void findScene();

  void updateHeadlamp();

  gz::rendering::ScenePtr scene;
  gz::rendering::MaterialPtr headlampMaterial;

  gz::transport::Node transportNode;

  std::atomic_bool requestedOn{false};
  bool appliedState{false};
  bool materialFound{false};
};

#endif
