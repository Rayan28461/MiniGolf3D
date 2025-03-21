using UnityEngine;

public class MeshCollisionDetector : MonoBehaviour
{
    public MeshFilter targetMeshFilter; // Assign in the Inspector
    public float maxRayDistance = 10f;

    private void Update()
    {
        DetectMeshIntersection();
    }

    public void DetectMeshIntersection()
    {
        if (targetMeshFilter == null)
        {
            Debug.LogWarning("Target MeshFilter is not assigned!");
            return;
        }

        Mesh mesh = targetMeshFilter.sharedMesh;
        Ray ray = new Ray(transform.position, transform.forward);
        RaycastHit hit;

        if (MeshRaycast(ray, mesh, out hit))
        {
            Debug.Log("Hit mesh at: " + hit.point);
        }
    }

    private bool MeshRaycast(Ray ray, Mesh mesh, out RaycastHit hit)
    {
        hit = new RaycastHit();
        Vector3[] vertices = mesh.vertices;
        int[] triangles = mesh.triangles;

        for (int i = 0; i < triangles.Length; i += 3)
        {
            Vector3 v0 = targetMeshFilter.transform.TransformPoint(vertices[triangles[i]]);
            Vector3 v1 = targetMeshFilter.transform.TransformPoint(vertices[triangles[i + 1]]);
            Vector3 v2 = targetMeshFilter.transform.TransformPoint(vertices[triangles[i + 2]]);

            if (RayIntersectsTriangle(ray, v0, v1, v2, out Vector3 intersection))
            {
                hit.point = intersection;
                return true;
            }
        }

        return false;
    }

    private bool RayIntersectsTriangle(Ray ray, Vector3 v0, Vector3 v1, Vector3 v2, out Vector3 intersection)
    {
        intersection = Vector3.zero;
        Vector3 edge1 = v1 - v0;
        Vector3 edge2 = v2 - v0;
        Vector3 h = Vector3.Cross(ray.direction, edge2);
        float a = Vector3.Dot(edge1, h);

        if (a > -0.00001f && a < 0.00001f)
            return false;

        float f = 1.0f / a;
        Vector3 s = ray.origin - v0;
        float u = f * Vector3.Dot(s, h);

        if (u < 0.0f || u > 1.0f)
            return false;

        Vector3 q = Vector3.Cross(s, edge1);
        float v = f * Vector3.Dot(ray.direction, q);

        if (v < 0.0f || u + v > 1.0f)
            return false;

        float t = f * Vector3.Dot(edge2, q);
        if (t > 0.00001f)
        {
            intersection = ray.origin + ray.direction * t;
            return true;
        }

        return false;
    }
}
