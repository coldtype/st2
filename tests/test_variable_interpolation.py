from .common import * #INLINE

bake_tag = "ST2:Text_BakedFrames_Anchor"

@b3d_runnable()
def test_variable_interpolation(bw:BpyWorld):
    def extrema(e1=0.1, e2=1):
        to1 = common(bw, bake_tag)
        to1.locate(-2, 2, 2)
        to1.obj.data.extrude = e1
        to1.obj.st2.fvar_axis1 = 0
        to1.select(False, set_active=True)

        bpy.ops.st2.settype_with_scene_defaults()
        to2 = BpyObj(bpy.context.object)
        to2.locate(2, -2, -2)
        to2.obj.data.extrude = e2
        to2.obj.st2.fvar_axis1 = 1
        to2.select(False, set_active=True)

        to1.select(True)
        to2.select(True)
        
        return to1, to2

    extrema()
    bw.scene.st2.interpolator_count = 1
    bw.scene.st2.interpolator_style = "TOP"
    bpy.ops.st2.interpolate_strings()

    to3 = BpyObj(bpy.context.object)
    assert to3.obj.location == vec(0,0,0), "location"
    assert len(bpy.context.selected_objects) == 1, "count"

    extrema()
    bw.scene.st2.interpolator_count = 3
    bpy.ops.st2.interpolate_strings()
    
    assert len(bpy.context.selected_objects) == 3, "count"
    example = bpy.context.selected_objects[1]
    assert example.data.extrude == pytest.approx(0.55), "extrusion"
    assert example.users_collection[0].name == "Collection", "top-level collection"

    extrema()
    bw.scene.st2.interpolator_count = 3
    bpy.ops.st2.interpolate_strings()
    
    assert len(bpy.context.selected_objects) == 3, "count"
    example = bpy.context.selected_objects[1]
    assert example.data.extrude == pytest.approx(0.55), "extrusion"
    assert example.users_collection[0].name == "Collection", "top-level collection"

    to1, to2 = extrema(0.01, 0.01)
    to1.rotate(z=45)
    to2.rotate(z=-45)
    bw.scene.st2.interpolator_count = 5
    bw.scene.st2.interpolator_style = "PARENT"
    bpy.ops.st2.interpolate_strings()

    assert len(bpy.context.selected_objects) == 5, "count"
    example = bpy.context.selected_objects[1]
    assert example.data.extrude == pytest.approx(0.01), "extrusion"
    assert example.users_collection[0].name == "Collection", "top-level collection"

    assert "InterpolationAnchor" in example.parent.name, "anchor"

    extrema(0.01, 0.01)
    bw.scene.st2.interpolator_count = 10
    bw.scene.st2.interpolator_style = "COLLECTION"
    bpy.ops.st2.interpolate_strings()

    assert len(bpy.context.selected_objects) == 10, "count"
    example = bpy.context.selected_objects[1]
    
    assert example.users_collection[0].name == "ST2:Interpolations", "non-top collection"