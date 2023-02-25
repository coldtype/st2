from .common import * #INLINE

bake_tag = "ST2:Text_BakedFrames_Anchor"

@b3d_runnable()
def test_bake_no_timing(bw:BpyWorld):
    to = common(bw, bake_tag)
    to.obj.data.extrude = 0.01
    
    bw.scene.frame_set(0)
    to.obj.location[2] = 0
    to.obj.keyframe_insert(data_path="location")
    to.obj.st2.fvar_axis1 = 0
    to.obj.keyframe_insert(data_path="st2.fvar_axis1")

    bw.scene.frame_set(29)
    to.obj.location[2] = -10
    to.obj.keyframe_insert(data_path="location")
    to.obj.st2.fvar_axis1 = 1
    to.obj.keyframe_insert(data_path="st2.fvar_axis1")

    bpy.ops.st2.bake_frames_no_timing()

    bake = BpyObj.Find(bake_tag)
    assert bake.obj is not None

    baked_frames = bake.find_children()
    assert len(baked_frames) == 30

    assert baked_frames[15].location[2] == pytest.approx(-5.2585, 1e-3)