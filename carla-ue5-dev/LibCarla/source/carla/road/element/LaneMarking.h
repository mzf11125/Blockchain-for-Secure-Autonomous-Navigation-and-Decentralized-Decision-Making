// Copyright (c) 2024 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include <cstdint>
#include <string>

namespace carla {
namespace road {
namespace element {

  class RoadInfoMarkRecord;

  struct LaneMarking {

    enum class Type {
      Other,
      Broken,
      Solid,
      // (for double solid line)
      SolidSolid,
      // (from inside to outside, exception: center lane -from left to right)
      SolidBroken,
      // (from inside to outside, exception: center lane -from left to right)
      BrokenSolid,
      // (from inside to outside, exception: center lane -from left to right)
      BrokenBroken,
      BottsDots,
      // (meaning a grass edge)
      Grass,
      Curb,
      None
    };

    enum class Color : uint8_t {
      Standard = 0u, // (equivalent to "white")
      Blue     = 1u,
      Green    = 2u,
      Red      = 3u,
      White    = Standard,
      Yellow   = 4u,
      Other    = 5u
    };

    /// Can be used as flags.
    enum class LaneChange : uint8_t {
      None  = 0x00, // 00
      Right = 0x01, // 01
      Left  = 0x02, // 10
      Both  = 0x03  // 11
    };

    explicit LaneMarking(const RoadInfoMarkRecord &info);

    Type type = Type::None;

    Color color = Color::Standard;

    LaneChange lane_change = LaneChange::None;

    double width = 0.0;

    std::string GetColorInfoAsString(){
      switch(color){
        case Color::Yellow:
          return std::string("yellow");
          break;
        case Color::Standard:
          return std::string("white");
          break;
        default:
          return std::string("white");
          break;
      }
      return std::string("white");
    }
  };

} // namespace element
} // namespace road
} // namespace carla
