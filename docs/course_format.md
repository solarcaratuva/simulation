# Course Definition File Format

Course definitions are JSON files stored in the repository's `courses/` directory. They describe the physical course and the location metadata needed to retrieve weather. Car parameters, weather assumptions, and race strategy settings remain separate inputs.

## File naming and loading

- Each course is stored in its own `.json` file.
- The simulator loads every JSON file in `courses/` through `get_available_tracks()`.
- `course_name_argument` is the value accepted by the `--location` command-line option.
- Course files are loaded in filename order for the interactive course list.
- The file name does not determine the command-line identifier; use
  `course_name_argument` for that identifier.
- Missing required fields or a non-numeric `lap_distance_m` value causes the
  course file to be rejected.

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `course_name` | string | Yes | Human-readable course or route name. |
| `course_name_argument` | string | Yes | Stable identifier used with `--location`. |
| `lap_distance_m` | number | Yes | One lap or route distance in meters. |
| `total_laps` | positive integer or `null` | No | Fixed number of laps when the event has one. Use `null` for time-window simulations; this is reserved for future fixed-lap support. |
| `elevation` | string or `null` | No | Elevation data or reference. Use `null` until elevation support is added. |
| `source` | string or `null` | No | Source for the course measurements or route data. Use `null` until source metadata is needed. |
| `location` | string | Yes | Human-readable location used in reports. |
| `latitude` | number | Yes | Latitude used for weather lookup, in degrees. |
| `longitude` | number | Yes | Longitude used for weather lookup, in degrees. |
| `timezone` | string | Yes | IANA timezone used for local race and weather times. |

`lap_distance_m` must be greater than zero. If `total_laps` is not `null`, it
must be greater than zero. The `total_laps`, `elevation`, and `source` fields
are currently future-capability placeholders and are stored as `null` in the
current course files. All distances are in meters.

At runtime, `TrackConfig.lap_distance_m` is the primary course-distance value.
`TrackConfig.lap_distance_km` is a derived property used only when kilometer
output is requested.

## Example

```json
{
  "course_name": "Shenandoah Speedway",
  "course_name_argument": "shenandoah_speedway",
  "lap_distance_m": 604,
  "total_laps": null,
  "elevation": null,
  "source": null,
  "location": "Page County, Virginia",
  "latitude": 38.511,
  "longitude": -78.6359,
  "timezone": "America/New_York"
}
```

`total_laps` is shown as `null` because the current simulator runs a race window and calculates completed laps from elapsed distance (future implementation for fixed-lap events). The `elevation` and `source` fields are also `null` because those are reserved for future capabilities.
