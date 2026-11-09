"""Write EnergyPlus 23.2 input files for the opaque BESTEST-style verification cases.

The IDFs reproduce, object for object, the ExoBEM cases in ``exobem.cases`` so that the
two engines can be compared on Earth (Golden, CO TMY3).  EnergyPlus settings are chosen
to match the algorithms ExoBEM implements: TARP inside/outside convection, Perez sky,
FullExterior solar distribution, Country terrain, 6 time steps per hour.
"""
from __future__ import annotations

import sys
from pathlib import Path

HEADER = """Version,23.2;
SimulationControl,No,No,No,No,Yes,No,1;
Building,{name},0,Country,0.04,0.004,FullExterior,25,6;
Timestep,6;
SurfaceConvectionAlgorithm:Inside,TARP;
SurfaceConvectionAlgorithm:Outside,TARP;
HeatBalanceAlgorithm,ConductionTransferFunction,200;
ZoneAirHeatBalanceAlgorithm,ThirdOrderBackwardDifference;
GlobalGeometryRules,UpperLeftCorner,Counterclockwise,Relative;
Site:Location,Golden CO,39.74,-105.18,-7.0,1829.0;
Site:GroundTemperature:BuildingSurface,10,10,10,10,10,10,10,10,10,10,10,10;
Site:GroundReflectance,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2;
RunPeriod,Annual,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
ScheduleTypeLimits,Any Number;
Schedule:Constant,AlwaysOn,Any Number,1.0;
Schedule:Constant,HeatSP,Any Number,{heat};
Schedule:Constant,CoolSP,Any Number,{cool};
Schedule:Constant,CtrlType,Any Number,4;
"""

MATERIALS = {
    "600": """
Material,WoodSiding,Rough,0.009,0.14,530,900,0.9,0.6,0.6;
Material,Fiberglass66,Rough,0.066,0.04,12,840,0.9,0.6,0.6;
Material,Plasterboard12,Smooth,0.012,0.16,950,840,0.9,0.6,0.6;
Material,RoofDeck19,Rough,0.019,0.14,530,900,0.9,0.6,0.6;
Material,Fiberglass1118,Rough,0.1118,0.04,12,840,0.9,0.6,0.6;
Material,Plasterboard10,Smooth,0.010,0.16,950,840,0.9,0.6,0.6;
Material,TimberFloor25,Rough,0.025,0.14,650,1200,0.9,0.6,0.6;
Material:NoMass,FloorIns,MediumRough,25.075,0.9,0.6,0.6;
Construction,Wall,WoodSiding,Fiberglass66,Plasterboard12;
Construction,Roof,RoofDeck19,Fiberglass1118,Plasterboard10;
Construction,Floor,FloorIns,TimberFloor25;
""",
    "900": """
Material,WoodSiding,Rough,0.009,0.14,530,900,0.9,0.6,0.6;
Material,FoamIns615,Rough,0.0615,0.04,10,1400,0.9,0.6,0.6;
Material,ConcreteBlock100,Rough,0.100,0.51,1400,1000,0.9,0.6,0.6;
Material,RoofDeck19,Rough,0.019,0.14,530,900,0.9,0.6,0.6;
Material,Fiberglass1118,Rough,0.1118,0.04,12,840,0.9,0.6,0.6;
Material,Plasterboard10,Smooth,0.010,0.16,950,840,0.9,0.6,0.6;
Material,ConcreteSlab80,Rough,0.080,1.13,1400,1000,0.9,0.6,0.6;
Material:NoMass,FloorIns,MediumRough,25.175,0.9,0.6,0.6;
Construction,Wall,WoodSiding,FoamIns615,ConcreteBlock100;
Construction,Roof,RoofDeck19,Fiberglass1118,Plasterboard10;
Construction,Floor,FloorIns,ConcreteSlab80;
""",
}

GEOMETRY = """
Zone,Zone1,0,0,0,0,1,1,2.7,129.6;
BuildingSurface:Detailed,wall_south,Wall,Wall,Zone1,,Outdoors,,SunExposed,WindExposed,0.5,4,
  0,0,2.7, 0,0,0, 8,0,0, 8,0,2.7;
BuildingSurface:Detailed,wall_east,Wall,Wall,Zone1,,Outdoors,,SunExposed,WindExposed,0.5,4,
  8,0,2.7, 8,0,0, 8,6,0, 8,6,2.7;
BuildingSurface:Detailed,wall_north,Wall,Wall,Zone1,,Outdoors,,SunExposed,WindExposed,0.5,4,
  8,6,2.7, 8,6,0, 0,6,0, 0,6,2.7;
BuildingSurface:Detailed,wall_west,Wall,Wall,Zone1,,Outdoors,,SunExposed,WindExposed,0.5,4,
  0,6,2.7, 0,6,0, 0,0,0, 0,0,2.7;
BuildingSurface:Detailed,roof,Roof,Roof,Zone1,,Outdoors,,SunExposed,WindExposed,0,4,
  0,6,2.7, 0,0,2.7, 8,0,2.7, 8,6,2.7;
BuildingSurface:Detailed,floor,Floor,Floor,Zone1,,Ground,,NoSun,NoWind,1,4,
  0,0,0, 0,6,0, 8,6,0, 8,0,0;
OtherEquipment,Gains,None,Zone1,AlwaysOn,EquipmentLevel,200,,,0,0.6,0;
ZoneInfiltration:DesignFlowRate,Infil,Zone1,AlwaysOn,AirChanges/Hour,,,,{ach},1,0,0,0;
"""

HVAC = """
ZoneControl:Thermostat,Zone1 Tstat,Zone1,CtrlType,ThermostatSetpoint:DualSetpoint,DualSP;
ThermostatSetpoint:DualSetpoint,DualSP,HeatSP,CoolSP;
ZoneHVAC:EquipmentConnections,Zone1,Zone1 Equipment,Zone1 Inlets,,Zone1 Air Node,Zone1 Return;
ZoneHVAC:EquipmentList,Zone1 Equipment,SequentialLoad,ZoneHVAC:IdealLoadsAirSystem,Zone1 Ideal,1,1,,;
NodeList,Zone1 Inlets,Zone1 Ideal Supply;
ZoneHVAC:IdealLoadsAirSystem,Zone1 Ideal,,Zone1 Ideal Supply,,,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,,,None,,None;
"""

OUTPUTS = """
Output:Variable,*,Zone Mean Air Temperature,Timestep;
Output:Variable,*,Zone Ideal Loads Zone Sensible Heating Rate,Timestep;
Output:Variable,*,Zone Ideal Loads Zone Sensible Cooling Rate,Timestep;
Output:Variable,*,Surface Inside Face Temperature,Hourly;
Output:Variable,*,Surface Outside Face Temperature,Hourly;
Output:Variable,*,Surface Outside Face Incident Solar Radiation Rate per Area,Hourly;
Output:Variable,*,Surface Outside Face Convection Heat Transfer Coefficient,Hourly;
Output:Variable,*,Surface Inside Face Convection Heat Transfer Coefficient,Hourly;
Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;
OutputControl:Table:Style,Comma;
Output:Table:SummaryReports,AllSummary;
"""


def make_idf(case="600", free_float=False, ach=0.5):
    name = f"Case{case}{'FF' if free_float else ''}_opaque"
    txt = HEADER.format(name=name, heat=20.0, cool=27.0)
    txt += MATERIALS[case]
    txt += GEOMETRY.format(ach=ach)
    if not free_float:
        txt += HVAC
    txt += OUTPUTS
    return name, txt


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "idf")
    out.mkdir(parents=True, exist_ok=True)
    for case in ("600", "900"):
        for ff in (False, True):
            name, txt = make_idf(case, ff)
            (out / f"{name}.idf").write_text(txt)
            print("wrote", out / f"{name}.idf")
