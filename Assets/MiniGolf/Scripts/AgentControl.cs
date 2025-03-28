using UnityEngine;
using UnityEngine.Networking;
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
    [SerializeField] private LayerMask rayLayer; // New: layer mask for raycasting
    private Rigidbody rgBody;
    private bool ballIsStatic = true;
    public int id;
    // New: Each agent will have its own shot count.
    public int shotCount;
    // Flag to ensure single shot request when ball stops
    private bool hasRequestedShot = false;

    [System.Serializable]
    public class EnvironmentData
    {
        public int agent_id;
        public Vector3 ball_position;
        public Vector3 hole_position;
        // Changed property name and type to match backend expectation.
        public Vector3[] walls;
    }

    IEnumerator PostEnvironmentData(EnvironmentData data)
    {
        string jsonData = JsonUtility.ToJson(data);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
        // updated backend url
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:8000/environment", "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Environment data sent successfully: " + request.downloadHandler.text);
        }
        else
        {
            Debug.LogError("Error sending environment data: " + request.error);
        }
    }

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
            // Compute raycast hit data using ClickedPoint.
            Vector3 raycastHit = ClickedPoint();
            GameManager.singleton.SendBallData(transform.position, "NearbyWalls");
            
            // Gather environment info.
            Vector3 currentBallPos = transform.position;
            Vector3 holePos = new Vector3(10, 0, 10); // Adjust as needed.
            
            // Wrap raycast hit into an array to send as walls.
            EnvironmentData envData = new EnvironmentData {
                agent_id = id,
                ball_position = currentBallPos,
                hole_position = holePos,
                walls = new Vector3[] { raycastHit }
            };
            StartCoroutine(PostEnvironmentData(envData));
            
            // Request shot with environment in one API call.
            yield return StartCoroutine(MiniGolfAPI.RequestShotWithEnvironment(id, currentBallPos, holePos, null, (shot) =>
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

    // Updated: method to perform raycast and return the clicked point
    private Vector3 ClickedPoint()
    {
        float sphereRadius = 5f; // adjust as needed
        Collider[] hitColliders = Physics.OverlapSphere(transform.position, sphereRadius, rayLayer, QueryTriggerInteraction.Collide);
        if (hitColliders.Length > 0)
        {
            Vector3 avgPoint = Vector3.zero;
            foreach (Collider hit in hitColliders)
            {
                avgPoint += hit.transform.position;
            }
            avgPoint /= hitColliders.Length;
            return avgPoint;
        }
        else
        {
            return transform.position;
        }
    }
}