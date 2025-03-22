using UnityEngine;
using System.Collections;

/// <summary>
/// Controls the AI golf ball based on API decisions.
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class AgentControl : MonoBehaviour
{
    public static AgentControl instance;

    [SerializeField] private float MaxForce = 5f;
    [SerializeField] private float stopThreshold = 0.1f; // velocity below which the ball is considered stopped
    private Rigidbody rgBody;
    private bool ballIsStatic = true;
    public int id;
    // New: Each agent will have its own shot count.
    public int shotCount;
    // Flag to ensure single shot request when ball stops
    private bool hasRequestedShot = false;

    private void Awake()
    {
        rgBody = GetComponent<Rigidbody>();
        shotCount = 5;
        // Start the coroutine to process shots for this agent
        StartCoroutine(ProcessShots());
    }

    IEnumerator ProcessShots()
    {
        while (shotCount > 0)
        {
            // Wait until the ball is stopped.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude < stopThreshold);
            
            // Decrement shot count and send ball data.
            shotCount--;
            GameManager.singleton.SendBallData(transform.position, "NearbyWalls");
            
            // Gather environment info.
            Vector3 currentBallPos = transform.position;
            Vector3 holePos = new Vector3(10, 0, 10); // Adjust as needed.
            Vector3[] walls = new Vector3[0];         // Adjust as needed.
            
            // Request shot with environment in one API call.
            yield return StartCoroutine(MiniGolfAPI.RequestShotWithEnvironment(id, currentBallPos, holePos, walls, (shot) =>
            {
                if (shot != null)
                {
                    ApplyShot(shot.power, shot.direction);
                }
                else
                {
                    Debug.Log("Shot API call failed for agent " + id);
                }
            }));
            
            // Wait until the ball has started moving.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude > stopThreshold);
            // Then wait until it stops again before next shot.
            yield return new WaitUntil(() => rgBody.linearVelocity.magnitude < stopThreshold);
        }
    }

    /// <summary>
    /// Applies the AI-calculated shot.
    /// </summary>
    public void ApplyShot(float power, Vector3 direction)
    {
        ballIsStatic = false;
        // Reset the flag so next stop triggers a new request
        hasRequestedShot = false;
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
            // NEW: Call the backend to deduct score for this agent.
            StartCoroutine(MiniGolfAPI.DeductScore(id, (response) =>
            {
                Debug.Log("Deduct score response for agent " + id + ": " + response);
            }));
            // Existing behavior: reposition the agent and halt movement.
            transform.position = new Vector3(0, 0.5f, 0);
            rgBody.linearVelocity = Vector3.zero;
        }
        else if (other.name == "Hole")
        {
            LevelManager.instance.LevelComplete();
        }
    }
}