from gossipsub_large_msg_lab.simulator import SimulationConfig, Simulator


def test_simulator_completes_without_loss_or_churn() -> None:
    config = SimulationConfig(
        peer_count=8,
        mesh_degree=3,
        segment_size=128,
        payload_size=512,
        fanout=3,
        loss_rate=0.0,
        duplicate_rate=0.0,
        churn_rate=0.0,
        max_rounds=1000,
        seed=3,
    )

    result = Simulator(config).run()

    assert result.segment_count == 4
    assert result.completed_peers == 7
    assert result.completion_rate == 1.0


def test_simulator_models_dropped_delivery() -> None:
    config = SimulationConfig(
        peer_count=8,
        mesh_degree=2,
        segment_size=128,
        payload_size=512,
        fanout=2,
        loss_rate=1.0,
        duplicate_rate=0.0,
        churn_rate=0.0,
        max_rounds=100,
        seed=4,
    )

    result = Simulator(config).run()

    assert result.completed_peers == 0
    assert result.dropped_events > 0


def test_simulator_records_churned_peers() -> None:
    config = SimulationConfig(
        peer_count=8,
        mesh_degree=2,
        payload_size=512,
        churn_rate=1.0,
        seed=5,
    )

    result = Simulator(config).run()

    assert result.churned_peers
    assert "peer-0" not in result.churned_peers
