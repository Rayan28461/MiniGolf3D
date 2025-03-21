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
        if (canShoot)                                               //if canSHoot is true
        {
            canShoot = false;                                       //set canShoot to false
            ballIsStatic = false;                                   //set ballIsStatic to false
            direction = startPos - endPos;                          //get the direction between 2 vectors from start to end pos
            // Zero out the vertical component to prevent bouncing on flat ground.
            direction.y = 0;
            if (force > 5)
                force = 5;
            rgBody.AddForce(direction * force, ForceMode.Impulse);  //add force to the ball in given direction
            areaAffector.SetActive(false);                          //deactivate areaAffector
            UIManager.instance.PowerBar.fillAmount = 0;             //reset the powerBar to zero
            force = 0;                                              //reset the force to zero
            startPos = endPos = Vector3.zero;                       //reset the vectors to zero
        }
    }

    // Unity native Method to detect colliding objects
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
