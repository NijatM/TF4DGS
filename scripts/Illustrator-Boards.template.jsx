#target illustrator
// Run from Illustrator: File > Scripts > Other Script.
// Creates the ORIGINAL boards as native AI; SVG edits are not imported.
// Existing native AI files are never overwritten. No network/system changes.
(function () {
    var boards = __BOARD_DATA__;
    var destination = File($.fileName).parent;
    var pt = 72 / 25.4;
    var oldCoordinates = app.coordinateSystem;
    var oldInteraction = app.userInteractionLevel;
    function ink(black) {
        var value = new CMYKColor();
        value.cyan = 0; value.magenta = 0; value.yellow = 0; value.black = black;
        return value;
    }
    function fill(item, black) {
        item.filled = true; item.stroked = false; item.fillColor = ink(black);
        item.opacity = 100;
    }
    try {
        for (var b = 0; b < boards.length; b++) {
            var target = new File(destination.fsName + '/' + boards[b].name + '.ai');
            if (target.exists) throw new Error('AI already exists: ' + target.fsName + '. Rename/move it to preserve your edits before rerunning.');
        }
        app.coordinateSystem = CoordinateSystem.DOCUMENTCOORDINATESYSTEM;
        app.userInteractionLevel = UserInteractionLevel.DISPLAYALERTS;
        for (var i = 0; i < boards.length; i++) {
            var data = boards[i];
            var height = data.height_mm * pt;
            var doc = app.documents.add(DocumentColorSpace.CMYK, data.width_mm * pt, height);
            doc.artboards[0].artboardRect = [0, height, data.width_mm * pt, 0];
            doc.artboards[0].name = data.name;
            doc.rulerUnits = RulerUnits.Millimeters;
            var initialLayer = doc.layers[0];
            for (var j = 0; j < data.layers.length; j++) {
                var objects = data.layers[j];
                var layer = doc.layers.add(); layer.name = objects.name;
                var k, item, values;
                for (k = 0; k < objects.rectangles.length; k++) {
                    values = objects.rectangles[k];
                    item = layer.pathItems.rectangle(height - values[2] * pt, values[1] * pt, values[3] * pt, values[4] * pt);
                    item.name = values[0]; fill(item, values[5]);
                }
                for (k = 0; k < objects.markers.length; k++) {
                    var marker = objects.markers[k];
                    var group = layer.groupItems.add(); group.name = marker.name;
                    var compound = group.compoundPathItems.add(); compound.name = marker.name + '_bits';
                    for (var r = 0; r < marker.rectangles.length; r++) {
                        values = marker.rectangles[r];
                        item = compound.pathItems.rectangle(height - values[1] * pt, values[0] * pt, values[2] * pt, values[3] * pt);
                        fill(item, 100);
                    }
                }
                for (k = 0; k < objects.lines.length; k++) {
                    values = objects.lines[k]; item = layer.pathItems.add();
                    item.name = values[0]; item.setEntirePath([[values[1] * pt, height - values[2] * pt], [values[3] * pt, height - values[4] * pt]]);
                    item.filled = false; item.stroked = true; item.strokeColor = ink(100); item.strokeWidth = 0.35;
                }
                for (k = 0; k < objects.texts.length; k++) {
                    values = objects.texts[k]; item = layer.textFrames.add();
                    item.name = values.name; item.contents = values.content;
                    item.textRange.characterAttributes.size = values.size_pt;
                    item.textRange.characterAttributes.fillColor = ink(100);
                    try { item.textRange.characterAttributes.textFont = app.textFonts.getByName('ArialMT'); }
                    catch (fontError) { /* Keep Illustrator's default live font. */ }
                    item.textRange.paragraphAttributes.justification = values.anchor === 'end' ? Justification.RIGHT : Justification.LEFT;
                    item.position = [values.x * pt, height - values.y * pt];
                    if (values.rotation) item.rotate(-values.rotation, true, true, true, true, Transformation.TOPLEFT);
                }
                if (objects.name === 'Paper') layer.locked = true;
            }
            initialLayer.remove();
            var options = new IllustratorSaveOptions();
            options.pdfCompatible = true; options.compressed = true;
            doc.saveAs(new File(destination.fsName + '/' + data.name + '.ai'), options);
        }
        alert('Saved two native AI files beside this script, with separate Paper, Checkerboard, Markers, Measurements and Labels layers. Verify the 100 mm rulers before printing an edited version.');
    } catch (error) {
        alert('TF4DGS Illustrator export: ' + error.message + '\nAny created document is left open for inspection.');
    } finally {
        app.coordinateSystem = oldCoordinates;
        app.userInteractionLevel = oldInteraction;
    }
}());
