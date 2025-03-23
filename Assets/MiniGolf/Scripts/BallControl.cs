using UnityEngine;
using System.Collections.Generic;
using Unity.Collections; // Required for NativeArray

/// <summary>
/// Script which controls the ball with ghost collision prevention
/// </summary>
[RequireComponent(typeof(Rigidbody), typeof(Collider))]
public class BallControl : MonoBehaviour
{
    public static BallControl instance;

    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private float MaxForce;
    [SerializeField] private float forceModifier = 0.5f;
    [SerializeField] private GameObject areaAffector;
    [SerializeField] private LayerMask rayLayer;
    
    // Ghost collision prevention
    [SerializeField] private PreventionMode BouncePreventionMode = PreventionMode.Simple;
    private Collider ballCollider;
    private int colliderInstanceId;
    
    private float force;
    private Rigidbody rgBody;
    private Vector3 startPos, endPos;
    private bool canShoot = false, ballIsStatic = true;
    private Vector3 direction;

    public float visionDistance = 10f;
    public float visionAngle = 90f;
    public int rayCount = 20;
    public LayerMask detectionLayer;
    
    public MeshCollisionDetector meshDetector;

    private enum PreventionMode
    {
        None,
        Simple
    }

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
        ballCollider = GetComponent<Collider>();
        
        // Configure collider for contact modification
        ballCollider.hasModifiableContacts = true;
        ballCollider.providesContacts = true;
        colliderInstanceId = ballCollider.GetInstanceID();
    }

    private void OnEnable()
    {
        Physics.ContactModifyEventCCD += PreventGhostBumpsCCD;
        Physics.ContactModifyEvent += PreventGhostBumpsCCD;
    }

    private void OnDisable()
    {
        Physics.ContactModifyEventCCD -= PreventGhostBumpsCCD;
        Physics.ContactModifyEvent -= PreventGhostBumpsCCD;
    }

    private void OnDestroy()
    {
        Physics.ContactModifyEventCCD -= PreventGhostBumpsCCD;
        Physics.ContactModifyEvent -= PreventGhostBumpsCCD;
    }

    // Ghost collision prevention logic
    private void PreventGhostBumpsCCD(PhysicsScene scene, NativeArray<ModifiableContactPair> contactPairs)
    {
        if (BouncePreventionMode != PreventionMode.Simple) return;

        for (int j = 0; j < contactPairs.Length; j++)
        {
            ModifiableContactPair pair = contactPairs[j];
            if (pair.colliderInstanceID == colliderInstanceId)
            {
                for (int i = 0; i < pair.contactCount; i++)
                {
                    if (pair.GetSeparation(i) > 0)
                    {
                        pair.IgnoreContact(i);
                    }
                }
            }
        }
    }

    // Rest of your original methods remain unchanged below
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
            direction.y = 0;
            if (force > 5)
                force = 5;
            rgBody.AddForce(direction * force, ForceMode.Impulse);
            areaAffector.SetActive(false);
            UIManager.instance.PowerBar.fillAmount = 0;
            force = 0;
            startPos = endPos = Vector3.zero;
        }
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
        RaycastHit hit;
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