from .common import * #INLINE

bake_tag = "ST2:Text_BakedFrames_Anchor"

@b3d_runnable()
def test_bake_timing(bw:BpyWorld):
    to = common(bw, bake_tag)
    to.obj.data.extrude = 1
    
    bw.scene.frame_set(0)
    to.obj.location[2] = 5
    to.obj.keyframe_insert(data_path="location")
    to.obj.st2.fvar_axis1 = 0
    to.obj.keyframe_insert(data_path="st2.fvar_axis1")
    to.obj.st2.fvar_axis2 = 0
    to.obj.keyframe_insert(data_path="st2.fvar_axis2")

    bw.scene.frame_set(29)
    to.obj.location[2] = -5
    to.obj.keyframe_insert(data_path="location")
    to.obj.st2.fvar_axis1 = 1
    to.obj.keyframe_insert(data_path="st2.fvar_axis1")
    to.obj.st2.fvar_axis2 = 1
    to.obj.keyframe_insert(data_path="st2.fvar_axis2")

    bpy.ops.st2.bake_frames()

    bake = BpyObj.Find(bake_tag)
    assert bake.obj is not None

    baked_frames = bake.find_children()
    assert len(baked_frames) == 30

    assert baked_frames[15].location[2] == pytest.approx(-0.2585, 1e-3)

    bw.scene.frame_set(15)
    assert baked_frames[0].scale == vec(0,0,0)
    assert baked_frames[14].scale == vec(0,0,0)
    assert baked_frames[15].scale == vec(1,1,1)

    bw.scene.frame_set(0)
    assert baked_frames[0].scale == vec(1,1,1)
    assert baked_frames[15].scale == vec(0,0,0)

    assert baked_frames[0].users_collection[0].name == "Collection"