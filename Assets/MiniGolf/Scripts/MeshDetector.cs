using UnityEngine;

public class MeshDetector : MonoBehaviour
{
    public float maxDistance = 10f; // Max raycast distance

    void Update()
    {
        Ray ray = new Ray(transform.position, transform.forward);
        RaycastHit hit;

        // Get all MeshColliders in the scene
        MeshCollider[] meshColliders = FindObjectsOfType<MeshCollider>();

        foreach (MeshCollider meshCollider in meshColliders)
        {
            if (meshCollider.Raycast(ray, out hit, maxDistance))
            {
                Debug.Log("Hit Mesh: " + hit.collider.name);
            }
        }
    }
}