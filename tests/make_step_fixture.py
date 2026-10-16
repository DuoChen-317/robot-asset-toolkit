"""Generate a redistributable coloured CAD test fixture with FreeCAD's Python."""
import argparse
import os
import sys
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    target = args.output.expanduser().resolve()
    if target.exists():
        raise ValueError('Refusing existing fixture: ' + str(target))
    if target.suffix.lower() not in ('.step', '.stp'):
        raise ValueError('Fixture output must be STEP/STP')
    sys.argv = ['FreeCAD']
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    import FreeCAD as App
    import FreeCADGui as Gui
    Gui.showMainWindow()
    Gui.getMainWindow().hide()
    import Part
    import ImportGui
    doc = App.newDocument('Fixture')
    root = doc.addObject('App::Part', 'Robot')
    root.Placement = App.Placement(App.Vector(120, -35, 80), App.Rotation(App.Vector(0, 0, 1), 30))
    group = doc.addObject('App::Part', 'Tool')
    root.addObject(group)
    group.Placement = App.Placement(App.Vector(15, 10, 25), App.Rotation(App.Vector(1, 0, 0), 20))
    box = doc.addObject('Part::Feature', 'Mount')
    root.addObject(box)
    box.Shape = Part.makeBox(20, 30, 10)
    box.ViewObject.ShapeColor = (0.8, 0.2, 0.1)
    box.Placement = App.Placement(App.Vector(5, 10, 0), App.Rotation())
    cylinder = doc.addObject('Part::Feature', 'ToolBody')
    group.addObject(cylinder)
    cylinder.Shape = Part.makeCylinder(5, 45)
    cylinder.ViewObject.ShapeColor = (0.1, 0.4, 0.8)
    doc.recompute()
    target.parent.mkdir(parents=True, exist_ok=True)
    ImportGui.export([root], str(target))
    App.closeDocument(doc.Name)
    print('Created fixture:', target, flush=True)


if __name__ == '__main__':
    status = 0
    try:
        main()
    except BaseException:
        traceback.print_exc()
        status = 1
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)
