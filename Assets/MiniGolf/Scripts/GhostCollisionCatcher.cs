using Unity.Collections;
using UnityEngine;

public class GhostCollisionCatcher : MonoBehaviour {

    private void OnEnable() {
        Physics.ContactModifyEvent += ModificationEventDCD;
        Physics.ContactModifyEventCCD += ModificationEventCCD;
        GetComponent<Collider>().hasModifiableContacts = true;
    }

    private void OnDisable() {
        Physics.ContactModifyEvent -= ModificationEventDCD;
        Physics.ContactModifyEventCCD -= ModificationEventCCD;
    }
    private void ModificationEventDCD( PhysicsScene scene, NativeArray<ModifiableContactPair> pairs ) {
        ModificationEvent( pairs );
    }
    private void ModificationEventCCD( PhysicsScene scene, NativeArray<ModifiableContactPair> pairs ) {
        ModificationEvent( pairs );
    }
    private void ModificationEvent( NativeArray<ModifiableContactPair> pairs ) {

        foreach ( var pair in pairs ) {
            for ( int i = 0; i < pair.contactCount; ++i ) {
                pair.SetNormal( i, Vector3.up );
            }
        }
    }
}