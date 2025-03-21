using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Script which controls the ball
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class BallControl : MonoBehaviour
{
    public static BallControl instance;

    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private float MaxForce;
    [SerializeField] private float forceModifier = 0.5f;
    [SerializeField] private GameObject areaAffector;
    [SerializeField] private LayerMask rayLayer;
    
    private float force;
    private Rigidbody rgBody;
    private Vector3 startPos, endPos;
    private bool canShoot = false, ballIsStatic = true;
    private Vector3 direction;

    // [SerializeField] private float rayDistance = 1.0f; // Distance for raycasting

    public float visionDistance = 10f; // How far the ball can see
    public float visionAngle = 90f;    // Field of view (FOV) in degrees
    public int rayCount = 20;          // Number of rays in the vision cone
    public LayerMask detectionLayer;   // Layers the ball can "see"
    
    public MeshCollisionDetector meshDetector;
    
    private void Awake()
    {
        if (instance == null)
        {
            instance = this;
        }
        else
        {
            Destroy(gameObject);
        }

        rgBody = GetComponent<Rigidbody>();
    }

    void Update()
    {
        if (rgBody.linearVelocity == Vector3.zero && !ballIsStatic)
        {
            ballIsStatic = true;
            LevelManager.instance.ShotTaken();
            rgBody.angularVelocity = Vector3.zero;
            areaAffector.SetActive(true);
        }
    }

    private void FixedUpdate()
    {
        if (canShoot)
        {
            canShoot = false;
            ballIsStatic = false;
            direction = startPos - endPos;
            rgBody.AddForce(direction * force, ForceMode.Impulse);
            areaAffector.SetActive(false);
            UIManager.instance.PowerBar.fillAmount = 0;
            force = 0;
            startPos = endPos = Vector3.zero;
        }

        // 🔴 **Added Raycasting Here**
        PerformRaycast();
        if (meshDetector != null)
        {
            Debug.Log("hello");
            meshDetector.DetectMeshIntersection();
        }
    }

    /// <summary>
    /// Detects objects in front of the ball using Raycast
    /// </summary>
    private void PerformRaycast()
    {
        List<string> seenObjects = new List<string>();

        // Get the forward direction of the ball
        Vector3 forward = transform.forward;

        for (int i = 0; i < rayCount; i++)
        {
            // Calculate spread of rays within visionAngle
            float angle = -visionAngle / 2 + (visionAngle / (rayCount - 1)) * i;
            Quaternion rotation = Quaternion.Euler(0, angle, 0);
            Vector3 rayDirection = rotation * forward;

            // Perform the raycast
            if (Physics.Raycast(transform.position, rayDirection, out RaycastHit hit, visionDistance, detectionLayer))
            {
                if (!seenObjects.Contains(hit.collider.name))
                {
                    seenObjects.Add(hit.collider.name);
                    Debug.Log("Ball sees: " + hit.collider.name);
                }
            }

            // Debug: Draw rays in Scene view
            Debug.DrawRay(transform.position, rayDirection * visionDistance, Color.green, 0.1f);
        }
    }
    
    private void OnDrawGizmos()
    {
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, 4f);
    }


    private void OnTriggerEnter(Collider other)
    {
        if (other.name == "Destroyer")
        {
            LevelManager.instance.LevelFailed();
        }
        else if (other.name == "Hole")
        {
            LevelManager.instance.LevelComplete();
        }
    }

    public void MouseDownMethod()
    {
        if (!ballIsStatic) return;
        startPos = ClickedPoint();
        lineRenderer.gameObject.SetActive(true);
        lineRenderer.SetPosition(0, lineRenderer.transform.localPosition);
    }

    public void MouseNormalMethod()
    {
        if (!ballIsStatic) return;
        endPos = ClickedPoint();
        force = Mathf.Clamp(Vector3.Distance(endPos, startPos) * forceModifier, 0, MaxForce);
        UIManager.instance.PowerBar.fillAmount = force / MaxForce;
        lineRenderer.SetPosition(1, transform.InverseTransformPoint(endPos));
    }

    public void MouseUpMethod()
    {
        if (!ballIsStatic) return;
        canShoot = true;
        lineRenderer.gameObject.SetActive(false);
    }

    Vector3 ClickedPoint()
    {
        Vector3 position = Vector3.zero;
        var ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        RaycastHit hit = new RaycastHit();
        if (Physics.Raycast(ray, out hit, Mathf.Infinity, rayLayer))
        {
            position = hit.point;
        }
        return position;
    }

#if UNITY_EDITOR
    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, 1.5f);
    }
#endif
}
