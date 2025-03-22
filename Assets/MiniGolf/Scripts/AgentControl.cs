using UnityEngine;

/// <summary>
/// Controls the AI golf ball based on API decisions.
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class AgentControl : MonoBehaviour
{
    public static AgentControl instance;

    [SerializeField] private float MaxForce = 5f;
    private Rigidbody rgBody;
    private bool ballIsStatic = true;
    public int id;

    private void Awake()
    {
        // if (instance == null)
        //     instance = this;
        // else
        //     Destroy(gameObject);

        rgBody = GetComponent<Rigidbody>();
    }

    private void Update()
    {
        if (rgBody.linearVelocity.magnitude < 0.1f && !ballIsStatic)
        {
            ballIsStatic = true;
            LevelManager.instance.ShotTaken();
            rgBody.linearVelocity = Vector3.zero;
            rgBody.angularVelocity = Vector3.zero;

            // Send ball position and request next shot
            GameManager.singleton.SendBallData(transform.position, "NearbyWalls"); // Change "NearbyWalls" based on actual objects
            GameManager.singleton.RequestShot();
        }
    }

    /// <summary>
    /// Applies the AI-calculated shot.
    /// </summary>
    public void ApplyShot(float power, Vector3 direction)
    {
        ballIsStatic = false;
        power = Mathf.Clamp(power, 0, MaxForce);

        // Zero out the vertical component to prevent bouncing.
        direction.y = 0;

        // Apply force
        rgBody.AddForce(direction.normalized * power, ForceMode.Impulse);
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
}